"""Add two passive text rows to the captured shared stat widget.

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
    vb_default = add('Default__VerticalBox', umg, 'VerticalBox', '/Script/UMG')
    vbs_default = add('Default__VerticalBoxSlot', umg, 'VerticalBoxSlot', '/Script/UMG')
    text_class = add('CommonTextBlock', common)
    text_default = add('Default__CommonTextBlock', common, 'CommonTextBlock', '/Script/CommonUI')
    style_pkg = package('/Game/UI/Common/Text/TextStyle/SystemText/BP_SystemTextStyle')
    style = add('BP_SystemTextStyle_C', style_pkg, 'BlueprintGeneratedClass', '/Script/Engine')
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
        prop('Slots', 'ArrayPropertyData', [prop(str(i), 'ObjectPropertyData', first + 1 + i * 2)
                                          for i in range(3)], ArrayType='ObjectProperty')])
    root['CreateBeforeSerializationDependencies'] = [first + 1, first + 3, first + 5]
    old_root['Data'].append(prop('Slot', 'ObjectPropertyData', original_slot))
    old_root['CreateBeforeSerializationDependencies'].append(original_slot)
    additions = [root, slot('VerticalBoxSlot_OriginalStats', old_root_index)]
    for i, kind in enumerate(('Physical', 'Magical')):
        text_index, slot_index = first + 2 + i * 2, first + 3 + i * 2
        title = copy.deepcopy(native['label'])
        data = [copy.deepcopy(p) for p in title['Data'] if p['Name'] not in ('Slot', 'Visibility')]
        next(p for p in data if p['Name'] == 'Style')['Value'] = style
        text = next(p for p in data if p['Name'] == 'Text')
        text.update(CultureInvariantString=f'{kind} Evasion: —', Value=f'Studio{kind}Evasion')
        data.extend([prop('Slot', 'ObjectPropertyData', slot_index),
                     prop('Visibility', 'EnumPropertyData', 'Collapsed', EnumType='ESlateVisibility', InnerType='ByteProperty')])
        name = 'Text_Studio' + kind + 'Evasion'
        title.update(ObjectName=name, ClassIndex=text_class, TemplateIndex=text_default,
                     OuterIndex=tree_index, Data=data)
        dependencies(title, before=(style, slot_index), classes=(text_class, text_default), outers=(tree_index,))
        additions.extend([title, slot('VerticalBoxSlot_' + kind + 'Evasion', text_index, 8 if i == 0 else 0)])
        reflected = copy.deepcopy(next(p for p in cls['LoadedProperties'] if p['Name'] == 'WBP_DirectionGridPanel'))
        reflected.update(Name=name, PropertyClass=text_class)
        cls['LoadedProperties'].append(reflected)
    exports.extend(additions)
    field(tree, 'RootWidget')['Value'] = root_index
    tree['CreateBeforeSerializationDependencies'].append(root_index)
    names(asset)
    return asset


def mappings(original, asset):
    """Extend this existing schema in a private copy; keep all schema indices.

    The captured mappings already contain this BP. The cave helper only adds
    absent schemas, so it cannot describe our two appended widget properties.
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
    if total != count or properties != [(i, 1, p['Name']) for i, p in enumerate(props[:-2])]:
        raise ValueError('Native stat-page schema changed')
    added = b''
    for i, prop_data in enumerate(props[-2:], count):
        if prop_data['SerializedType'] != 'ObjectProperty': raise ValueError('Expected text widget properties')
        strings.append(prop_data['Name'])
        added += binary.pack('<HBiB', i, 1, len(strings)-1, 4)
    header = binary.pack('<iiHH', name, parent, total+2, count+2)
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
