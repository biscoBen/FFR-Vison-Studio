"""Read the pinned UE5.6 icon's native mip stream, including its bulk table.

UAssetAPI roundtrip treats this body as opaque Extras. Follow the independent
CUE4Parse FByteBulkDataHeader data-resource lookup/classic-header fallback and
the captured single-mip BGRA8 texture layout instead of only comparing bytes.
This is a narrow offline validator, not an Unreal/game rendering test.
"""
import base64
import struct


def native_read(asset):
    export = asset['Exports'][0]
    raw = base64.b64decode(export['Extras'], validate=True)
    prefix = export['SerialSize'] - len(raw)
    index = struct.unpack_from('<i', raw, 80)[0]
    resources = asset.get('DataResources') or []
    if asset.get('DataResourceVersion') == 'Initial' and 0 <= index < len(resources):
        resource = resources[index]
        size = resource['RawSize']
        cursor = 84
    else:
        # The broken 1.2.163 stream has index 352 followed by transparent
        # zero pixels. With no resource table it is read as a classic header:
        # flags, element count, disk size, 64-bit offset. That consumes 20
        # bytes and declares an empty mip, exactly as in the reported crash.
        flags, size, disk_size, offset = struct.unpack_from('<IIIq', raw, 80)
        if flags != 352 or size or disk_size or offset:
            raise ValueError('Unsupported classic bulk header in private UE5.6 icon')
        resource = None
        cursor = 100
    pixels = raw[cursor:cursor + size]
    cursor += size
    dimensions = struct.unpack_from('<3I', raw, cursor)
    cursor += 12
    virtual = struct.unpack_from('<I', raw, cursor)[0]
    cursor += 4
    terminator, instance = struct.unpack_from('<II', raw, cursor)
    cursor += 8
    return {'consumed': prefix + cursor, 'expected': export['SerialSize'],
            'prefix': prefix, 'index': index, 'resource': resource,
            'pixels': pixels, 'dimensions': dimensions, 'virtual': virtual,
            'terminator': asset['NameMap'][terminator], 'instance': instance,
            'raw': raw}


def validate(asset):
    result = native_read(asset)
    resource = result['resource']
    if resource is None:
        raise ValueError(f"Missing texture bulk-data table: native read {result['consumed']}, expected {result['expected']}")
    if result['index'] != 0 or len(asset['DataResources']) != 1:
        raise ValueError('Private icon must reference its own single bulk entry')
    if (resource['SerialSize'] != 65536 or resource['RawSize'] != 65536
            or resource['SerialOffset'] != result['prefix'] + 84
            or resource['LegacyBulkDataFlags'] != 72 or resource['OuterIndex'] != 0):
        raise ValueError('Unsupported icon bulk size, inline offset or flags')
    if (result['consumed'] != result['expected'] or len(result['pixels']) != 65536
            or result['dimensions'] != (128, 128, 1) or result['virtual']
            or result['terminator'] != 'None' or result['instance']):
        raise ValueError('Icon native mip stream does not consume its full export')
    raw = result['raw']
    if (raw[60:72] != b'PF_B8G8R8A8\0'
            or asset['NameMap'][struct.unpack_from('<I', raw, 12)[0]] != 'PF_B8G8R8A8'
            or struct.unpack_from('<I', raw, 20)[0] != len(raw) - 28
            or struct.unpack_from('<3I', raw, 44) != (128, 128, 1)
            or struct.unpack_from('<2I', raw, 72) != (0, 1)):
        raise ValueError('Icon platform format or skip offset is invalid')
    return result
