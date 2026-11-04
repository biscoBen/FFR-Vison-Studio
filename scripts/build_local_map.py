"""Author a third native local-map step from Ben's read-only map capture.

Compile with the pinned ffr-dt SDK and the capture's original Mappings.usmap.
World/airship overrides, native view entries and the map widget stay intact.
"""
import copy
import gzip
import json
from pathlib import Path

FIXTURE = Path(__file__).with_name('fixtures') / 'local_map_native.json.gz'
BASE = 'FFRS/Content/UI/Field/MiniMap/Data/'
# Existing registered parent of all four native keys; no invented gameplay tag.
FULL = 'UI.Field.MiniMap.View.Decrale'


def field(properties, name):
    return next(p for p in properties if p['Name'] == name)


def set_value(properties, name, value):
    prop = field(properties, name)
    prop.update(Value=value, IsZero=False)


def author(native):
    from build_treasure_ui import names
    result = copy.deepcopy(native['assets'])
    properties = result['DA_MiniMapProperty']['Exports'][0]['Data']
    steps = field(field(field(properties, 'DefaultProperty')['Value'],
                        'DisplayStepPropertySet')['Value'], 'PropertyList')['Value']
    assert len(steps) == 2
    step = copy.deepcopy(steps[0])
    set_value(field(step['Value'], 'ViewPropertyTag')['Value'], 'TagName', FULL)
    steps.insert(1, step)
    for index, item in enumerate(steps):
        item['Name'] = str(index)

    views = field(result['DA_MiniMapViewProperty']['Exports'][0]['Data'], 'PropertyMap')['Value']
    key, value = copy.deepcopy(next(pair for pair in views
        if field(pair[0]['Value'], 'TagName')['Value'] == FULL + '.Instance'))
    set_value(key['Value'], 'TagName', FULL)
    props = value['Value']
    set_value(props, 'OriginType', 'Image')
    set_value(props, 'DisplayScale', 2.4)
    set_value(props, 'ZoomAlpha', 0.0)
    set_value(props, 'bUseSaveZoomAlpha', False)
    zoom = field(props, 'ZoomProperty')['Value']
    for interval, scale in [('AlphaInterval', 0.0), ('ScaleInterval', 0.1)]:
        set_value(zoom, 'bOverride' + interval, True)
        for end in ('min', 'max'):
            set_value(field(zoom, interval)['Value'], end, scale)
    views.append([key, value])
    for asset in result.values():
        names(asset)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    native = json.loads(gzip.decompress(FIXTURE.read_bytes()))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, asset in author(native).items():
        (args.output / (name + '.json')).write_text(json.dumps(asset), encoding='utf-8')
