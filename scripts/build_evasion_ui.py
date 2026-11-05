"""Add two passive label/value rows to the captured shared stat widget.

The original grid, bytecode, bindings and stat enums remain intact. Unreal owns
all children from its cooked WidgetTree; Lua only updates text and visibility.
Compile/read back with pinned ffr-dt and the capture's original Mappings.usmap.
"""
import copy
import gzip
import json
import struct as binary
from pathlib import Path

from build_treasure_ui import dependencies, field, importer, names, prop, struct

FIXTURE = Path(__file__).with_name('fixtures') / 'evasion_ui_native.json.gz'
ASSET = 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail'


def author(native):
    asset = copy.deepcopy(native['widget'])
    exports = asset['Exports']
    cls = next(e for e in exports if e['ObjectName'] == 'WBP_UnitParam_Detail_C')
    tree = next(e for e in exports if e['ObjectName'] == 'WidgetTree')
    tree_index = exports.index(tree) + 1
    old_root_index = field(tree, 'RootWidget')['Value']
    old_root = exports[old_root_index - 1]
    assert old_root['ObjectName'] == 'Overlay_0'
    add, package = importer(asset)
    umg = package('/Script/UMG')
    common = package('/Script/CommonUI')
    vb, vbs = add('VerticalBox', umg), add('VerticalBoxSlot', umg)
    hb, hbs = add('HorizontalBox', umg), add('HorizontalBoxSlot', umg)
    vb_default = add('Default__VerticalBox', umg, 'VerticalBox', '/Script/UMG')
    vbs_default = add('Default__VerticalBoxSlot', umg, 'VerticalBoxSlot', '/Script/UMG')
    hb_default = add('Default__HorizontalBox', umg, 'HorizontalBox', '/Script/UMG')
    hbs_default = add('Default__HorizontalBoxSlot', umg, 'HorizontalBoxSlot', '/Script/UMG')
    text_class = add('CommonTextBlock', common)
    text_default = add('Default__CommonTextBlock', common, 'CommonTextBlock', '/Script/CommonUI')
    style_pkg = package('/Game/UI/Common/Text/TextStyle/SystemText/BP_SystemTextStyle')
    style = add('BP_SystemTextStyle_C', style_pkg, 'BlueprintGeneratedClass', '/Script/Engine')
    number_pkg = package('/Game/UI/Common/Text/TextStyle/SystemText/BP_SystemTextStyle_PramNUM')
    number_style = add('BP_SystemTextStyle_PramNUM_C', number_pkg, 'BlueprintGeneratedClass', '/Script/Engine')
    first = len(exports) + 1
    root_index, original_slot = first, first + 1

    def widget(name, class_index, template, outer, data):
        result = copy.deepcopy(old_root)
        result.update(ObjectName=name, ClassIndex=class_index, TemplateIndex=template,
                      OuterIndex=outer, Data=data)
        dependencies(result, classes=(class_index, template), outers=(outer,))
        return result

    def slot(name, content, top=0):
        result = widget(name, vbs, vbs_default, root_index, [
            struct('Size', 'SlateChildSize', [prop('Value', 'FloatPropertyData', 1.0),
                prop('SizeRule', 'EnumPropertyData', 'Automatic', EnumType='ESlateSizeRule', InnerType='ByteProperty')]),
            struct('Padding', 'Margin', [prop('Top', 'FloatPropertyData', float(top))]),
            prop('HorizontalAlignment', 'EnumPropertyData', 'HAlign_Fill', EnumType='EHorizontalAlignment', InnerType='ByteProperty'),
            prop('Parent', 'ObjectPropertyData', root_index), prop('Content', 'ObjectPropertyData', content)])
        result['CreateBeforeSerializationDependencies'].append(content)
        return result

    root = widget('VerticalBox_StudioStats', vb, vb_default, tree_index, [
        prop('Slots', 'ArrayPropertyData', [prop(str(i), 'ObjectPropertyData', index)
            for i,index in enumerate((first+1,first+3,first+9))], ArrayType='ObjectProperty')])
    root['CreateBeforeSerializationDependencies'] = [first + 1, first + 3, first + 9]
    old_root['Data'].append(prop('Slot', 'ObjectPropertyData', original_slot))
    old_root['CreateBeforeSerializationDependencies'].append(original_slot)
    additions = [root, slot('VerticalBoxSlot_OriginalStats', old_root_index)]
    for i, (kind, short) in enumerate((('Physical','Phys. Eva'), ('Magical','Mag. Eva'))):
        row, row_slot = first+2+i*6, first+3+i*6
        label, label_slot, number, number_slot = row+2, row+3, row+4, row+5
        horizontal = widget('HorizontalBox_Studio'+kind+'Evasion', hb, hb_default, tree_index, [
            prop('Slots','ArrayPropertyData',[prop('0','ObjectPropertyData',label_slot),
                prop('1','ObjectPropertyData',number_slot)],ArrayType='ObjectProperty'),
            prop('Slot','ObjectPropertyData',row_slot)])
        horizontal['CreateBeforeSerializationDependencies'] = [row_slot,label_slot,number_slot]
        additions.extend([horizontal,slot('VerticalBoxSlot_'+kind+'Evasion',row,8 if i==0 else 0)])
        for is_number,index,slot_index in ((False,label,label_slot),(True,number,number_slot)):
            title = copy.deepcopy(native['number' if is_number else 'label'])
            data = [copy.deepcopy(p) for p in title['Data'] if p['Name'] not in ('Slot','Visibility')]
            text_style = number_style if is_number else style
            next(p for p in data if p['Name']=='Style')['Value'] = text_style
            if is_number:
                # The native numeric template's design-time magenta is normally
                # replaced by SyncVariation. These are current values, so use
                # the captured ordinary label's white instead of that preview.
                color = next(p for p in data if p['Name']=='ColorAndOpacity')
                color.update(copy.deepcopy(field(native['label'],'ColorAndOpacity')))
            field_name = 'Text_Studio'+kind+'Evasion'+('Value' if is_number else '')
            text = next(p for p in data if p['Name']=='Text')
            text.update(CultureInvariantString='—' if is_number else short,Value=field_name)
            data.extend([prop('Slot','ObjectPropertyData',slot_index),
                prop('Visibility','EnumPropertyData','Collapsed',EnumType='ESlateVisibility',InnerType='ByteProperty')])
            title.update(ObjectName=field_name,ClassIndex=text_class,TemplateIndex=text_default,
                         OuterIndex=tree_index,Data=data)
            dependencies(title,before=(text_style,slot_index),classes=(text_class,text_default),outers=(tree_index,))
            child_slot = widget('HorizontalBoxSlot_Studio'+kind+('Value' if is_number else 'Label'),
                hbs,hbs_default,row,[
                    struct('Size','SlateChildSize',[prop('Value','FloatPropertyData',1.0),
                        prop('SizeRule','EnumPropertyData','Automatic' if is_number else 'Fill',
                            EnumType='ESlateSizeRule',InnerType='ByteProperty')]),
                    struct('Padding','Margin',[prop('Right' if is_number else 'Left','FloatPropertyData',4.0 if is_number else 24.0)]),
                    prop('HorizontalAlignment','EnumPropertyData','HAlign_Right' if is_number else 'HAlign_Fill',
                        EnumType='EHorizontalAlignment',InnerType='ByteProperty'),
                    prop('VerticalAlignment','EnumPropertyData','VAlign_Center',EnumType='EVerticalAlignment',InnerType='ByteProperty'),
                    prop('Parent','ObjectPropertyData',row),prop('Content','ObjectPropertyData',index)])
            child_slot['CreateBeforeSerializationDependencies'] = [index]
            additions.extend([title,child_slot])
            reflected = copy.deepcopy(next(p for p in cls['LoadedProperties'] if p['Name']=='WBP_DirectionGridPanel'))
            reflected.update(Name=field_name,PropertyClass=text_class)
            cls['LoadedProperties'].append(reflected)
    exports.extend(additions)
    field(tree, 'RootWidget')['Value'] = root_index
    tree['CreateBeforeSerializationDependencies'].append(root_index)
    names(asset)
    return asset


def mappings(original, asset):
    """Extend this existing schema in a private copy; keep all schema indices.

    The captured mappings already contain this BP. The cave helper only adds
    absent schemas, so it cannot describe our appended widget properties.
    Preserve every unrelated schema, enum and count-delimited CEXT extension.
    """
    cls = next(e for e in asset['Exports'] if e['ObjectName'] == 'WBP_UnitParam_Detail_C')
    if (original[:8] != b'\xc4\x30\x04\x00\x00\x00\x00\x00' or
            original[8:12] != original[12:16] or
            len(original) != 16 + binary.unpack_from('<I', original, 8)[0]):
        raise ValueError('Expected uncompressed v4 native mappings')
    data, pos = original[16:], 0
    def take(fmt):
        nonlocal pos
        value = binary.unpack_from('<' + fmt, data, pos)
        pos += binary.calcsize('<' + fmt)
        return value[0] if len(value) == 1 else value
    strings = []
    for _ in range(take('i')):
        size = take('h')
        if size < 0: raise ValueError('Invalid mapping name')
        strings.append(data[pos:pos+size].decode('utf-8')); pos += size
    names_end = pos
    for _ in range(take('i')):
        take('i'); count = take('h'); pos += count * 12
    def skip():
        kind = take('B')
        if kind == 26: skip(); take('i')
        elif kind == 9: take('i')
        elif kind in (8, 25, 28): skip()
        elif kind == 24: skip(); skip()
        elif not 0 <= kind <= 30: raise ValueError('Invalid mapping type')
    target = None
    for _ in range(take('i')):
        start = pos
        name, parent, total, count = take('iiHH')
        properties = []
        for _ in range(count):
            index, dim, prop_name = take('HBi'); skip()
            properties.append((index, dim, strings[prop_name]))
        if strings[name] == cls['ObjectName']:
            target = start, pos, name, parent, total, count, properties
    if data[pos:] and data[pos:pos+4] != b'CEXT':
        raise ValueError('Unsupported mapping extensions')
    if target is None: raise ValueError('Native stat-page schema is absent')
    start, end, name, parent, total, count, properties = target
    props = cls['LoadedProperties']
    if total != count or properties != [(i, 1, p['Name']) for i, p in enumerate(props[:count])]:
        raise ValueError('Native stat-page schema changed')
    added = b''
    for i, prop_data in enumerate(props[count:], count):
        if prop_data['SerializedType'] != 'ObjectProperty': raise ValueError('Expected text widget properties')
        strings.append(prop_data['Name'])
        added += binary.pack('<HBiB', i, 1, len(strings)-1, 4)
    header = binary.pack('<iiHH', name, parent, len(props), len(props))
    encoded = [s.encode('utf-8') for s in strings]
    names_data = binary.pack('<i',len(strings)) + b''.join(binary.pack('<h',len(s))+s for s in encoded)
    result = names_data + data[names_end:start] + header + data[start+12:end] + added + data[end:]
    return original[:8] + binary.pack('<II',len(result),len(result)) + result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--mappings', type=Path)
    args = parser.parse_args()
    native = json.loads(gzip.decompress(FIXTURE.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    asset = author(native)
    args.output.write_text(json.dumps(asset), encoding='utf-8')
    if args.mappings:
        args.output.with_suffix('.usmap').write_bytes(mappings(args.mappings.read_bytes(), asset))
