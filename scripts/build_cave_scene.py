#!/usr/bin/env python3
"""Build the placement preview from decoded native entrance meshes/prop bounds.

Does not bake game shaders. Bounds are placement references, not claims about
walkability. Native input JSON remains outside the repository.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from build_acquisition_locations import ENTRANCES, mesh
from build_cave_terrain import fields, vector


def bounds(document):
    value = next(fields(e)['ExtendedBounds'] for e in document['Exports'] if 'ExtendedBounds' in fields(e))
    return vector(value.get('Origin') or dict(X=0, Y=0, Z=0)), vector(value['BoxExtent'])


def build(entrances, world, props, output):
    result = {'schema': 1, 'meshes': {}, 'props': [], 'sources': {}}
    for id, _, name, _, _ in ENTRANCES:
        p = entrances / (name + '.json')
        d = json.loads(p.read_text(encoding='utf-8-sig'))
        vertices, _, triangles = mesh(d)
        center, half = bounds(d)
        scale = 120.52937316894531 * .8 / max(half[:2])
        result['meshes'][id] = {
            'vertices': [[round((v[0] - center[0]) * scale, 4), round((v[1] - center[1]) * scale, 4),
                          round((v[2] - center[2] + half[2]) * scale, 4)] for v in vertices],
            'triangles': [list(t) for t, _ in triangles]}
        result['sources'][name] = hashlib.sha256(p.read_bytes()).hexdigest()
    native = json.loads(world.read_text(encoding='utf-8-sig'))
    result['sources'][world.stem] = hashlib.sha256(world.read_bytes()).hexdigest()
    for e in native['Exports']:
        if not isinstance(e.get('Data'), list): continue
        f = fields(e)
        if f.get('StaticMesh', 0) >= 0: continue
        item = native['Imports'][-f['StaticMesh'] - 1]
        path = props / (item['ObjectName'] + '.json')
        if not path.is_file(): continue
        d = json.loads(path.read_text(encoding='utf-8-sig'))
        origin, half = bounds(d)
        # All current native prop components are unparented root components.
        # Do not guess transforms for an unsupported hierarchy.
        if f.get('AttachParent', 0): continue
        location = vector(f.get('RelativeLocation', dict(X=0, Y=0, Z=0)))
        scales = vector(f.get('RelativeScale3D', dict(X=1, Y=1, Z=1)))
        rotation = next(iter(f.get('RelativeRotation', {'r': dict(Pitch=0, Yaw=0, Roll=0)}).values()))
        if float(rotation.get('Pitch', 0)) or float(rotation.get('Roll', 0)): continue
        yaw = math.radians(float(rotation.get('Yaw', 0))); c, s = math.cos(yaw), math.sin(yaw)
        corners = []
        for signs in itertools.product((-1, 1), repeat=3):
            x, y, z = [(origin[i] + signs[i] * half[i]) * scales[i] for i in range(3)]
            corners.append([round(location[0] + x * c - y * s, 3), round(location[1] + x * s + y * c, 3), round(location[2] + z, 3)])
        result['props'].append({'name': item['ObjectName'], 'corners': corners})
        result['sources'][path.stem] = hashlib.sha256(path.read_bytes()).hexdigest()
    output.write_text(json.dumps(result, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Built four entrance meshes and {len(result["props"])} native prop outlines.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--entrances', type=Path, required=True)
    p.add_argument('--world', type=Path, required=True)
    p.add_argument('--props', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('assets/acquisition_map/placement_scene.json'))
    a = p.parse_args(); build(a.entrances, a.world, a.props, a.output)
