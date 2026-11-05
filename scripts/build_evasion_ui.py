"""Add two passive label/value rows to the captured shared stat widget.

The original grid, class schema, bytecode, bindings and stat enums remain intact.
Unreal owns all children from its cooked WidgetTree; Lua updates their labels
and arranges the existing grid's native slots and spacer widgets.
Compile/read back with pinned ffr-dt and the capture's original Mappings.usmap.
"""
import copy
import base64
import gzip
import json
import struct as binary
from pathlib import Path

from build_treasure_ui import dependencies, field, importer, names, prop, struct

FIXTURE = Path(__file__).with_name('fixtures') / 'evasion_ui_native.json.gz'
ASSET = 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail'
STATUS_LIST = 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitStatus_DetailList'
ICON_BASE = 'FFRS/Content/UI/Studio/Evasion/T_Evasion'


def icon_textures(native):
    """Package the approved artwork as private inline BGRA8 UI textures.

    Use the captured native texture format, a single 128px mip and no external
    bulk file. No official icon or texture package is replaced.
    """
    from PIL import Image
    result = {}
    for kind in ('Physical', 'Magical'):
        image = Image.open(FIXTURE.parent / 'evasion_icons' / (kind.lower() + '.png')).convert('RGBA')
        if image.size != (128, 128): raise ValueError('Expected a 128px RGBA stat icon')
        pixels = image.tobytes('raw', 'BGRA')
        asset = copy.deepcopy(native['iconTexture']['asset'])
        name = 'T_Evasion' + kind
        asset['FolderName'] = '/Game/UI/Studio/Evasion/' + name
        export = asset['Exports'][0]
        export['ObjectName'] = name
        header = bytearray.fromhex(native['iconTexture']['header'])
        # The platform-data marker and final terminator are serialized FNames,
        # even though UAssetAPI exposes this native block as opaque Extras.
        # Relocate both against this private texture's name table.
        binary.pack_into('<II', header, 12, asset['NameMap'].index('PF_B8G8R8A8'), 0)
        binary.pack_into('<I', header, 20, 84 + len(pixels) + 24 - 28)
        binary.pack_into('<I', header, 76, 1)
        # UE5.6 writes a bulk-data MAP INDEX here, not a classic inline bulk
        # header. The extracted terrain donor used index 352; this private
        # single-mip texture owns entry zero. Without the table Unreal reads
        # the first transparent pixels as zero-sized classic bulk metadata.
        binary.pack_into('<I', header, 80, 0)
        asset['DataResourceVersion'] = 'Initial'
        asset['DataResources'] = [{
            '$type': 'UAssetAPI.UnrealTypes.FObjectDataResource, UAssetAPI',
            'Flags': 'None', 'CookedIndex': 0,
            'SerialOffset': native['iconTexture']['serializedPropertyBytes'] + len(header),
            'DuplicateSerialOffset': -1, 'SerialSize': len(pixels), 'RawSize': len(pixels),
            'OuterIndex': 0, 'LegacyBulkDataFlags': 72}]
        export['Extras'] = base64.b64encode(header + pixels + binary.pack('<3I', 128, 128, 1)
                                          + binary.pack('<3I', 0, asset['NameMap'].index('None'), 0)).decode()
        names(asset)
        result[name] = asset
    return result


def author(native):
    asset = copy.deepcopy(native['widget'])
    exports = asset['Exports']
    cls = next(e for e in exports if e['ObjectName'] == 'WBP_UnitParam_Detail_C')
    tree = next(e for e in exports if e['ObjectName'] == 'WidgetTree')
    tree_index = exports.index(tree) + 1
    old_root_index = field(tree, 'RootWidget')['Value']
    old_root = exports[old_root_index - 1]
    assert old_root['ObjectName'] == 'Overlay_0'
    native_grid_slot = exports[field(old_root, 'Slots')['Value'][0]['Value'] - 1]
    alignment = field(native_grid_slot, 'VerticalAlignment')
    assert alignment['Value'] == 'VAlign_Center'
    # The added rows contribute to Overlay desired height. Keeping the native
    # grid centred in that changing height moves it into the fallback rows.
    alignment['Value'] = 'VAlign_Top'
    add, package = importer(asset)
    umg = package('/Script/UMG')
    common = package('/Script/CommonUI')
    vb, vbs = add('VerticalBox', umg), add('VerticalBoxSlot', umg)
    hb, hbs = add('HorizontalBox', umg), add('HorizontalBoxSlot', umg)
    vb_default = add('Default__VerticalBox', umg, 'VerticalBox', '/Script/UMG')
    vbs_default = add('Default__VerticalBoxSlot', umg, 'VerticalBoxSlot', '/Script/UMG')
    hb_default = add('Default__HorizontalBox', umg, 'HorizontalBox', '/Script/UMG')
    hbs_default = add('Default__HorizontalBoxSlot', umg, 'HorizontalBoxSlot', '/Script/UMG')
    overlay_slot_class = add('OverlaySlot', umg)
    overlay_slot_default = add('Default__OverlaySlot', umg, 'OverlaySlot', '/Script/UMG')
    spacer_class = add('Spacer', umg)
    spacer_default = add('Default__Spacer', umg, 'Spacer', '/Script/UMG')
    text_class = add('CommonTextBlock', common)
    text_default = add('Default__CommonTextBlock', common, 'CommonTextBlock', '/Script/CommonUI')
    image_class = add('Image', umg)
    image_default = add('Default__Image', umg, 'Image', '/Script/UMG')
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
    for i, (kind, short) in enumerate((('Physical','Phys. Eva.'), ('Magical','Mag. Eva.'))):
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
            next(p for p in data if p['Name']=='bIsVariable').update(Value=False,IsZero=False)
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
                    struct('Padding','Margin',[prop('Right' if is_number else 'Left','FloatPropertyData',4.0)]),
                    prop('HorizontalAlignment','EnumPropertyData','HAlign_Right' if is_number else 'HAlign_Fill',
                        EnumType='EHorizontalAlignment',InnerType='ByteProperty'),
                    prop('VerticalAlignment','EnumPropertyData','VAlign_Center',EnumType='EVerticalAlignment',InnerType='ByteProperty'),
                    prop('Parent','ObjectPropertyData',row),prop('Content','ObjectPropertyData',index)])
            child_slot['CreateBeforeSerializationDependencies'] = [index]
            additions.extend([title,child_slot])
    exports.extend(additions)
    # The native stat icon occupies 32 Slate units, followed by a four-unit
    # gap. Use the same actual columns rather than a text-only left indent.
    icon_size = field(native['iconLayout']['box'], 'WidthOverride')['Value']
    assert icon_size == field(native['iconLayout']['box'], 'HeightOverride')['Value'] == 32.0
    for i, kind in enumerate(('Physical', 'Magical')):
        row = first + 2 + i * 6
        index, slot_index = len(exports) + 1, len(exports) + 2
        path = '/Game/UI/Studio/Evasion/T_Evasion' + kind
        texture = add('T_Evasion' + kind, package(path), 'Texture2D', '/Script/Engine')
        image_size = struct('ImageSize', 'DeprecateSlateVector2D', [
            prop('ImageSize', 'DeprecateSlateVector2DPropertyData',
                 {'$type': 'UAssetAPI.UnrealTypes.FVector2f, UAssetAPI', 'X': icon_size, 'Y': icon_size},
                 **{'$type': 'UAssetAPI.PropertyTypes.Structs.DeprecateSlateVector2DPropertyData, UAssetAPI'})])
        brush = copy.deepcopy(field(native['image'], 'Brush'))
        next(p for p in brush['Value'] if p['Name'] == 'ResourceObject')['Value'] = texture
        brush['Value'].append(image_size)
        image = widget('Image_Studio' + kind + 'Evasion', image_class, image_default, tree_index, [
            brush, prop('Slot', 'ObjectPropertyData', slot_index),
            prop('Visibility', 'EnumPropertyData', 'Collapsed', EnumType='ESlateVisibility', InnerType='ByteProperty')])
        dependencies(image, before=(texture, slot_index), classes=(image_class, image_default), outers=(tree_index,))
        icon_slot = widget('HorizontalBoxSlot_Studio' + kind + 'Icon', hbs, hbs_default, row, [
            prop('VerticalAlignment', 'EnumPropertyData', 'VAlign_Center', EnumType='EVerticalAlignment', InnerType='ByteProperty'),
            prop('Parent', 'ObjectPropertyData', row), prop('Content', 'ObjectPropertyData', index)])
        icon_slot['CreateBeforeSerializationDependencies'] = [index]
        horizontal = exports[row - 1]
        slots = field(horizontal, 'Slots')['Value']
        slots.insert(0, prop('0', 'ObjectPropertyData', slot_index))
        for j, value in enumerate(slots): value['Name'] = str(j)
        horizontal['CreateBeforeSerializationDependencies'].append(slot_index)
        exports.extend([image, icon_slot])
    # Leave every native grid entry in its own native grid. The passive rows
    # share the original overlay; native grid spacers reserve Defence gaps.
    # Keep the existing zero-size trailing spacer/tree shape for compatibility.
    reserve, reserve_slot = len(exports) + 1, len(exports) + 2
    for i, kind in enumerate(('Physical', 'Magical')):
        row, row_slot = first + 2 + i * 6, first + 3 + i * 6
        exports[row_slot - 1] = widget('OverlaySlot_Studio' + kind + 'Evasion',
            overlay_slot_class, overlay_slot_default, old_root_index, [
                struct('Padding', 'Margin', [prop('Top', 'FloatPropertyData', 0.0)]),
                prop('HorizontalAlignment', 'EnumPropertyData', 'HAlign_Fill', EnumType='EHorizontalAlignment', InnerType='ByteProperty'),
                prop('VerticalAlignment', 'EnumPropertyData', 'VAlign_Top', EnumType='EVerticalAlignment', InnerType='ByteProperty'),
                prop('Parent', 'ObjectPropertyData', old_root_index), prop('Content', 'ObjectPropertyData', row)])
        exports[row_slot - 1]['CreateBeforeSerializationDependencies'] = [row]
        field(old_root, 'Slots')['Value'].append(prop(str(i + 1), 'ObjectPropertyData', row_slot))
        old_root['CreateBeforeSerializationDependencies'].append(row_slot)
    field(root, 'Slots')['Value'] = [prop(str(i), 'ObjectPropertyData', index)
        for i, index in enumerate((original_slot, reserve_slot))]
    root['CreateBeforeSerializationDependencies'] = [original_slot, reserve_slot]
    space = widget('Spacer_StudioEvasionRoom', spacer_class, spacer_default, tree_index, [
        struct('Size', 'Vector2D', [prop('Size', 'Vector2DPropertyData',
            {'$type': 'UAssetAPI.UnrealTypes.FVector2D, UAssetAPI', 'X': 0.0, 'Y': 0.0},
            **{'$type': 'UAssetAPI.PropertyTypes.Structs.Vector2DPropertyData, UAssetAPI'})]),
        prop('Slot', 'ObjectPropertyData', reserve_slot)])
    exports.extend([space, slot('VerticalBoxSlot_StudioEvasionRoom', reserve)])
    field(tree, 'RootWidget')['Value'] = root_index
    tree['CreateBeforeSerializationDependencies'].append(root_index)
    names(asset)
    return asset


def status_list(native):
    asset = copy.deepcopy(native['statusList'])
    # Role and its text stay where they are. This is the existing spacer
    # immediately before the Attributes subhead, not a global font/scale edit.
    gap = next(e for e in asset['Exports'] if e['ObjectName'] == 'Spacer_142')
    size = field(gap, 'Size')['Value'][0]['Value']
    assert size['Y'] == 60.0
    size['Y'] = 24.0
    return asset


def mappings(original, asset):
    """Keep the original schema used by every embedded native instance.

    Adding BP fields shifts inherited unversioned property indices in other
    packages' existing child-widget data. A self-consistent roundtrip of this
    one modified class cannot establish compatibility with those instances.
    Text objects stay in WidgetTree without adding reflected class properties.
    """
    cls = next(e for e in asset['Exports'] if e['ObjectName'] == 'WBP_UnitParam_Detail_C')
    native = json.loads(gzip.decompress(FIXTURE.read_bytes()))['widget']
    baseline = next(e for e in native['Exports'] if e['ObjectName'] == cls['ObjectName'])
    if cls['LoadedProperties'] != baseline['LoadedProperties']:
        raise ValueError('Shared native stat-widget schema must remain unchanged')
    if (original[:8] != b'\xc4\x30\x04\x00\x00\x00\x00\x00' or
            original[8:12] != original[12:16] or
            len(original) != 16 + binary.unpack_from('<I', original, 8)[0]):
        raise ValueError('Expected uncompressed v4 native mappings')
    return original


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
    for name, texture in icon_textures(native).items():
        (args.output.parent / (name + '.json')).write_text(json.dumps(texture), encoding='utf-8')
    (args.output.parent / 'WBP_UnitStatus_DetailList.json').write_text(json.dumps(status_list(native)), encoding='utf-8')
    if args.mappings:
        args.output.with_suffix('.usmap').write_bytes(mappings(args.mappings.read_bytes(), asset))
