"""Author the reviewed native minimap counter and a passive status UserWidget.

Inputs are captured native metadata, not an installed observer. The counter reads
the game's saved collection flags; neither widget sends input or writes saves.
"""
import copy
import gzip
import json
from pathlib import Path

FIXTURE = Path(__file__).with_name('fixtures') / 'treasure_ui_native.json.gz'
STATUS = 'FFRS/Content/UI/Studio/WBP_StudioStatus'
MINIMAP = 'FFRS/Content/UI/Field/MiniMap/Widget/WBP_MiniMap'


def catalog_from_native(native):
    groups, coverage, ignored = {}, {}, []
    for row in native['maps']:
        if row['MapType'] not in ('Dungeon', 'VisionSmallShrine') and not row['Level'].startswith('/Game/Map/Dng/'):
            continue
        identity = row['ID']
        group_id = row['GroupId'] if row['GroupId'] >= 0 else identity
        group = groups.setdefault(group_id, {'maps': [], 'locations': {}})
        group['maps'].append(identity)
        # sameMapId is a saved namespace, and need not itself have a map row.
        saved_map = row['sameMapId'] if row['sameMapId'] >= 0 else identity
        todo, seen = [row['Level'].removeprefix('/Game/') + '.umap'], set()
        while todo:
            level = todo.pop()
            if level in seen: continue
            seen.add(level)
            source = native['levels'][level]  # Missing floors cannot become zero remaining.
            todo.extend(source['gameplayLevels'])
            for actor in source['collectibles']:
                props, cls = actor['properties'], actor['class']
                if props.get('m_IsOpen') is True:
                    ignored.append((level, actor['name'])); continue
                if props.get('m_FlagCondition') or props.get('m_VisibleCondition'):
                    raise ValueError('Unreviewed conditional collectible: ' + actor['name'])
                typed_id = props['TypeData'].get('ID', 0)
                unique_id = props.get('m_UniqueId', typed_id)
                if unique_id != typed_id: raise ValueError('Native collectible ID mismatch')
                kind = 'fragment' if 'Medal' in cls else 'pickup' if 'FieldItem' in cls else 'chest'
                key = (saved_map, unique_id)
                record = {'map': saved_map, 'uid': unique_id, 'kind': kind,
                          'source': level, 'actor': actor['name']}
                old = group['locations'].get(key)
                if old and old['kind'] != kind: raise ValueError('Conflicting collectible identity')
                if not old: group['locations'][key] = record
        coverage[str(identity)] = sorted(seen)
    return {'groups': [{'maps': sorted(g['maps']),
             'locations': sorted(g['locations'].values(), key=lambda l: (l['map'], l['uid']))}
             for _, g in sorted(groups.items())], 'coverage': coverage, 'ignored': ignored}


def prop(name, kind, value, **extra):
    category = 'Structs' if kind == 'StructPropertyData' else 'Objects'
    return {'$type': f'UAssetAPI.PropertyTypes.{category}.{kind}, UAssetAPI',
            'Name': name, 'ArrayIndex': 0, 'PropertyGuid': None, 'IsZero': False,
            'PropertyTagFlags': 'None', 'PropertyTypeName': None,
            'PropertyTagExtensions': 'NoExtension', 'Value': value, **extra}


def struct(name, kind, value):
    return prop(name, 'StructPropertyData', value, StructType=kind, SerializeNone=True,
                StructGUID='{00000000-0000-0000-0000-000000000000}',
                SerializationControl='NoExtension', Operation='None')


def field(export, name):
    return next(p for p in export['Data'] if p['Name'] == name)


def expr(kind, **values):
    return {'$type': 'UAssetAPI.Kismet.Bytecode.Expressions.' + kind + ', UAssetAPI', **values}


def size(node):
    op = node['$type'].split('.')[-1].split(',')[0]
    if op == 'EX_StringConst': return len(node['Value'].encode()) + 2
    if op == 'EX_LocalVariable': return 9
    if op == 'EX_IntConst': return 5
    if op == 'EX_EndOfScript': return 1
    if op == 'EX_CallMath': return 10 + sum(map(size, node['Parameters']))
    if op == 'EX_Return': return 1 + size(node['ReturnExpression'])
    if op == 'EX_JumpIfNot': return 5 + size(node['BooleanExpression'])
    if op == 'EX_Let': return 9 + size(node['Variable']) + size(node['Expression'])
    raise ValueError('Unsupported counter bytecode: ' + op)


def importer(asset):
    def add(name, owner=0, class_name='Class', class_package='/Script/CoreUObject'):
        value = {'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': name,
                 'OuterIndex': owner, 'ClassPackage': class_package,
                 'ClassName': class_name, 'PackageName': None, 'bImportOptional': False}
        if value not in asset['Imports']: asset['Imports'].append(value)
        return -(asset['Imports'].index(value) + 1)
    def package(name): return add(name, class_name='Package')
    return add, package


def names(asset):
    # IoStore can reference only this prefix. Include every added property,
    # function and package name using the existing native name collector.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'assets/existing_visions/payload'))
    import _ffr_crystal_cave as caves
    caves.names(asset, [asset['Imports'], asset['Exports']])


def dependencies(export, *, before=(), classes=(), outers=()):
    export.update(SerializationBeforeSerializationDependencies=[],
                  CreateBeforeSerializationDependencies=list(before),
                  SerializationBeforeCreateDependencies=list(classes),
                  CreateBeforeCreateDependencies=list(outers))


def text_export(asset, template, outer, slot=0):
    add, package = importer(asset)
    umg = package('/Script/UMG')
    cls = add('TextBlock', umg)
    default = add('Default__TextBlock', umg, 'TextBlock', '/Script/UMG')
    font_package = package('/Engine/EngineFonts/Roboto')
    font = add('Roboto', font_package, 'Font', '/Script/Engine')
    result = copy.deepcopy(template)
    text = copy.deepcopy(field(template, 'Text'))
    text.update(CultureInvariantString='', Value='StudioStatusText')
    color = copy.deepcopy(field(template, 'ColorAndOpacity'))
    color['Value'][0]['Value'][0]['Value'].update(R=1.0, G=1.0, B=1.0, A=1.0)
    result.update(ObjectName='Text_Name', OuterIndex=outer, ClassIndex=cls,
                  TemplateIndex=default, Data=[text, color,
                  struct('Font', 'SlateFontInfo', [prop('FontObject', 'ObjectPropertyData', font),
                      prop('TypefaceFontName', 'NamePropertyData', 'Regular'),
                      prop('Size', 'FloatPropertyData', 18.0)]),
                  prop('bIsVariable', 'BoolPropertyData', True),
                  prop('Visibility', 'EnumPropertyData', 'HitTestInvisible',
                       EnumType='ESlateVisibility', InnerType='ByteProperty'),
                  prop('Slot', 'ObjectPropertyData', slot)])
    dependencies(result, classes=(cls, default), outers=(outer,))
    return result, cls


def status_widget(native):
    original = native['keyGuide']
    asset = copy.deepcopy(original)
    text, text_class = text_export(asset, original['Exports'][0], 4)
    cdo = copy.deepcopy(original['Exports'][14])
    cdo.update(ObjectName='Default__WBP_StudioStatus_C', ClassIndex=3,
               Data=[p for p in cdo['Data'] if p['Name'] in
                     ('bHasScriptImplementedTick', 'bHasScriptImplementedPaint')])
    dependencies(cdo, classes=(3, cdo['TemplateIndex']))
    cls = copy.deepcopy(original['Exports'][15])
    text_property = copy.deepcopy(next(p for p in cls['LoadedProperties'] if p['Name'] == 'Text_Name'))
    text_property['PropertyClass'] = text_class
    cls.update(ObjectName='WBP_StudioStatus_C', ClassDefaultObject=2,
               FuncMap=[], Children=[], LoadedProperties=[text_property],
               ScriptBytecode=[], ScriptBytecodeSize=0, ScriptBytecodeRaw=None,
               Data=[prop('WidgetTree', 'ObjectPropertyData', 4)])
    dependencies(cls, before=(4,), classes=(cls['SuperStruct'], cls['TemplateIndex']))
    tree = copy.deepcopy(original['Exports'][16])
    tree.update(OuterIndex=3, Data=[prop('RootWidget', 'ObjectPropertyData', 1)])
    dependencies(tree, before=(1,), classes=(tree['ClassIndex'], tree['TemplateIndex']), outers=(3,))
    asset['Exports'] = [text, cdo, cls, tree]
    # Keep the source's serialization version, replace only its own package name.
    old = '/Game/UI/MainMenu/Common/Key/KeyGuide/WBP_KeyGuide'
    new = STATUS.replace('FFRS/Content/', '/Game/')
    # Cooked UE5 package identity comes from the legacy summary, not its output
    # filename. Retoc otherwise registers this private asset as WBP_KeyGuide.
    asset['FolderName'] = new
    asset['NameMap'] = [new if n == old else n for n in asset['NameMap']]
    names(asset)
    return asset


def counter_widget(native):
    asset = copy.deepcopy(native['miniMap'])
    exports = asset['Exports']
    cls = next(e for e in exports if e['ObjectName'] == 'WBP_MiniMap_C')
    class_index = exports.index(cls) + 1
    tree = next(e for e in exports if e['ObjectName'] == 'WidgetTree')
    root = exports[field(tree, 'RootWidget')['Value'] - 1]
    assert root['ObjectName'] == 'Overlay_4', 'The native unrotated minimap root changed'
    root_index = exports.index(root) + 1
    function_index, text_index, slot_index = len(exports)+1, len(exports)+2, len(exports)+3
    text, text_class = text_export(asset, native['keyGuide']['Exports'][0], exports.index(tree)+1, slot_index)
    text['ObjectName'] = 'Text_StudioRemaining'
    # UWidgetBlueprintGeneratedClass initializes bindings through the reflected
    # widget property, not a WidgetTree name lookup alone.
    widget_property = copy.deepcopy(next(p for p in cls['LoadedProperties']
                                         if p['SerializedType'] == 'ObjectProperty'))
    widget_property.update(Name='Text_StudioRemaining',PropertyClass=text_class)
    cls['LoadedProperties'].append(widget_property)
    # The counter stays on the unrotated root, above the native map content.
    slot = copy.deepcopy(exports[38])
    slot.update(ObjectName='OverlaySlot_StudioRemaining', OuterIndex=root_index,
                Data=[prop('HorizontalAlignment','EnumPropertyData','HAlign_Left',
                           EnumType='EHorizontalAlignment',InnerType='ByteProperty'),
                      prop('VerticalAlignment','EnumPropertyData','VAlign_Bottom',
                           EnumType='EVerticalAlignment',InnerType='ByteProperty'),
                      struct('Padding','Margin',[prop(k,'FloatPropertyData',8.0) for k in ('Left','Bottom')]),
                      prop('Parent','ObjectPropertyData',root_index),
                      prop('Content','ObjectPropertyData',text_index)])
    dependencies(slot, before=(text_index,), classes=(slot['ClassIndex'],slot['TemplateIndex']),outers=(root_index,))
    slots = field(root,'Slots')['Value']
    slots.append(prop(str(len(slots)),'ObjectPropertyData',slot_index))
    root['CreateBeforeSerializationDependencies'].append(slot_index)

    add, package = importer(asset)
    mucha = package('/Script/mucha'); engine = package('/Script/Engine')
    owners = {n:add(n,mucha) for n in ('CPP_BFL_Map','CPP_BFL_SaveDataMap')}
    owners.update({n:add(n,engine) for n in ('KismetMathLibrary','KismetStringLibrary','KismetTextLibrary')})
    functions = {}
    for owner, identifiers in (
        ('CPP_BFL_Map',('GetCurrentMapId',)),('CPP_BFL_SaveDataMap',('IsOpenTreasureBox',)),
        ('KismetMathLibrary',('EqualEqual_IntInt','BooleanOR','Add_IntInt','SelectInt')),
        ('KismetStringLibrary',('Conv_IntToString','Concat_StrStr')),
        ('KismetTextLibrary',('Conv_StringToText',))):
        for name in identifiers:functions[name] = add(name,owners[owner],'Function')
    call = lambda n,*args:expr('EX_CallMath',StackNode=functions[n],Parameters=list(args))
    integer = lambda n:expr('EX_IntConst',Value=n)
    pointer = lambda n:{'$type':'UAssetAPI.Kismet.Bytecode.KismetPropertyPointer, UAssetAPI',
        'New':{'$type':'UAssetAPI.UnrealTypes.FFieldPath, UAssetAPI','Path':[n],'ResolvedOwner':function_index}}
    local = lambda n:expr('EX_LocalVariable',Variable=pointer(n))
    function = copy.deepcopy(next(e for e in exports if e.get('FunctionFlags') and 'FUNC_BlueprintPure' in e['FunctionFlags']))
    base_property = {'ArrayDim':'TArray','PropertyFlags':'CPF_Parm, CPF_OutParm, CPF_ReturnParm',
        'RepIndex':0,'RepNotifyFunc':'None','BlueprintReplicationCondition':'COND_None',
        'RawValue':None,'Name':'ReturnValue','Flags':'RF_Public','MetaDataMap':None}
    returned = {'$type':'UAssetAPI.FieldTypes.FGenericProperty, UAssetAPI','ElementSize':16,
                'SerializedType':'TextProperty',**base_property}
    map_local = {**base_property,'$type':'UAssetAPI.FieldTypes.FGenericProperty, UAssetAPI','ElementSize':4,
                 'SerializedType':'IntProperty','PropertyFlags':'CPF_None','Name':'CurrentMap'}
    code = [expr('EX_Let',Value=pointer('CurrentMap'),Variable=local('CurrentMap'),Expression=call('GetCurrentMapId'))]
    for group in native['catalog']['groups']:
        matches = [call('EqualEqual_IntInt',local('CurrentMap'),integer(i)) for i in group['maps']]
        test = matches[0]
        for other in matches[1:]:test=call('BooleanOR',test,other)
        branch = expr('EX_JumpIfNot',CodeOffset=0,BooleanExpression=test)
        total = integer(0)
        for location in group['locations']:
            total = call('Add_IntInt',total,call('SelectInt',integer(0),integer(1),
                call('IsOpenTreasureBox',integer(location['map']),integer(location['uid']))))
        label = call('Conv_StringToText',call('Concat_StrStr',expr('EX_StringConst',Value='Items left: '),call('Conv_IntToString',total)))
        code.extend([branch,expr('EX_Return',ReturnExpression=label)])
        branch['CodeOffset'] = sum(map(size,code))
    code.extend([expr('EX_Return',ReturnExpression=call('Conv_StringToText',expr('EX_StringConst',Value=''))),expr('EX_EndOfScript')])
    function.update(ObjectName='GetStudioRemainingText',OuterIndex=class_index,
                    LoadedProperties=[returned,map_local],Children=[],Data=[],
                    ScriptBytecode=code,ScriptBytecodeSize=sum(map(size,code)),ScriptBytecodeRaw=None)
    dependencies(function,classes=(function['ClassIndex'],function['TemplateIndex']),outers=(class_index,))
    cls['FuncMap'].append(['GetStudioRemainingText',function_index]);cls['Children'].append(function_index)
    cls['CreateBeforeSerializationDependencies'].append(function_index)
    binding = struct('0','DelegateRuntimeBinding',[
        prop('ObjectName','StrPropertyData','Text_StudioRemaining'),
        prop('PropertyName','NamePropertyData','Text'),prop('FunctionName','NamePropertyData','GetStudioRemainingText'),
        struct('SourcePath','DynamicPropertyPath',[]),
        prop('Kind','EnumPropertyData','Function',EnumType='EBindingKind',InnerType='ByteProperty')])
    assert not any(p['Name']=='Bindings' for p in cls['Data'])
    cls['Data'].append(prop('Bindings','ArrayPropertyData',[binding],ArrayType='StructProperty'))
    exports.extend([function,text,slot]);names(asset)
    return asset


def load_native():
    native = json.loads(gzip.decompress(FIXTURE.read_bytes()))
    native['catalog'] = catalog_from_native(native)
    return native


def private_mappings(original, native):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'assets/existing_visions/payload'))
    import _ffr_crystal_cave as caves
    found = {}
    for qualified, source in native['schemaSources'].items():
        value = (source['view'], source['class'])
        found[qualified] = value
        found[source['class']['ObjectName']] = value
    return caves.map_mappings(original, found)


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path)
    p.add_argument('--mappings',type=Path);args=p.parse_args()
    native=load_native();args.output.mkdir(parents=True,exist_ok=True)
    for name,asset in (('status',status_widget(native)),('counter',counter_widget(native))):
        (args.output/(name+'.json')).write_text(json.dumps(asset,ensure_ascii=False),encoding='utf-8')
    if args.mappings:
        (args.output/'ui-mappings.usmap').write_bytes(private_mappings(args.mappings.read_bytes(),native))
    print('Authored native status widget and saved-state dungeon counter metadata.')
