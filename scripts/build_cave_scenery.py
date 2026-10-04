#!/usr/bin/env python3
"""Build an offline, shaded placement scene from private native world assets.

Reads native landscape paint and instanced-foliage matrices, retaining the full
component hierarchy. Uses diffuse sampling rather than emulating Unreal shaders.
Original game packages and the decoder cache remain outside the repository.
"""
import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import subprocess
import zipfile

import numpy as np
from PIL import Image

from build_acquisition_locations import diffuse, mesh
from build_cave_terrain import fields, vector


def matrix(f):
    yaw, pitch, roll = [math.radians(float(next(iter(f.get('RelativeRotation', {'r': {}}).values())).get(k, 0)))
                        for k in ('Yaw', 'Pitch', 'Roll')]
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    # UE FRotationMatrix, transposed for column-vector composition.
    rot = np.array([[cp*cy, sr*sp*cy-cr*sy, -(cr*sp*cy+sr*sy)],
                    [cp*sy, sr*sp*sy+cr*cy, cy*sr-cr*sp*sy], [sp, -sr*cp, cr*cp]])
    out = np.eye(4)
    out[:3, :3] = rot @ np.diag(vector(f.get('RelativeScale3D', dict(X=1, Y=1, Z=1))))
    out[:3, 3] = vector(f.get('RelativeLocation', dict(X=0, Y=0, Z=0)))
    return out


def component_matrix(document, index, visited=()):
    if index in visited or index <= 0: raise ValueError('Invalid native component hierarchy.')
    f = fields(document['Exports'][index - 1]); result = matrix(f)
    if f.get('AttachParent'): result = component_matrix(document, f['AttachParent'], visited + (index,)) @ result
    return result


def foliage_matrices(export):
    f = fields(export); count = f['NumBuiltInstances']
    raw = base64.b64decode(export['Extras'], validate=True)
    # Checked UE5.6 FInstancedStaticMeshInstanceData: LWC FMatrix (16 doubles).
    # Preceded by cooked lighting GUIDs, serialization flags and stride/count.
    guid_count = struct.unpack_from('<I', raw, 4)[0]
    start = 8 + guid_count * 34 + 16
    stride, size = struct.unpack_from('<2I', raw, start)
    start += 8
    if stride != 128 or size != count or start + count * stride > len(raw):
        raise ValueError('Unsupported native foliage instance buffer.')
    values = np.frombuffer(raw, '<f8', count * 16, start).reshape(count, 4, 4)
    if not np.isfinite(values).all() or not np.allclose(values[:, :, 3], [0, 0, 0, 1]):
        raise ValueError('Invalid native foliage matrices.')
    # Matrices already contain their local translation. Do not add
    # TranslatedInstanceSpaceOrigin again; attach-parent translation is separate.
    return values.transpose(0, 2, 1)


def weightmap(export):
    raw = base64.b64decode(export['Extras'], validate=True)
    w, h, depth, n = struct.unpack_from('<4I', raw, 44)
    end = 60 + n; start = end + 12
    if (raw[60:end] != b'PF_B8G8R8A8\0' or (w, h, depth) != (128, 128, 1)
            or struct.unpack_from('<3I', raw, start + w*h*4) != (w, h, 1)):
        raise ValueError('Unsupported native weightmap mip0.')
    return np.frombuffer(raw, np.uint8, w*h*4, start).reshape(h, w, 4)[:, :, [2, 1, 0, 3]]


class NativeAssets:
    def __init__(self, roots, cache, sdk, mapping):
        self.roots, self.cache, self.sdk, self.mapping = roots, cache, sdk, mapping
        cache.mkdir(parents=True, exist_ok=True)
        self.sources = {}; self.images = {}; self.docs = {}

    def package(self, document, ref):
        if ref >= 0: raise ValueError('Expected a native imported asset.')
        value = document['Imports'][-ref-1]
        parent = document['Imports'][-value['OuterIndex']-1]
        return parent['ObjectName']

    def path(self, package):
        if not package.startswith('/Game/'): raise ValueError('Unexpected native package path.')
        rel = package.removeprefix('/Game/')
        for root in self.roots:
            p = root / (rel + '.uasset')
            if p.exists(): return p
        raise FileNotFoundError(package)

    def load(self, package):
        if package in self.docs: return self.docs[package]
        p = self.path(package); digest = hashlib.sha256(p.read_bytes() + p.with_suffix('.uexp').read_bytes()).hexdigest()
        target = self.cache / (p.stem + '-' + digest[:12] + '.json')
        if not target.exists():
            r = subprocess.run(self.sdk + ['tojson', str(p), str(target), '--usmap', str(self.mapping)], capture_output=True, text=True)
            if r.returncode or 'roundtrip=False' in r.stdout: raise ValueError(r.stdout + r.stderr)
        self.sources[package] = digest
        self.docs[package] = json.loads(target.read_text(encoding='utf-8-sig'))
        return self.docs[package]

    def image(self, package):
        if package not in self.images:
            p = self.path(package); bulk = p.with_suffix('.ubulk')
            self.images[package] = diffuse(self.load(package), bulk.read_bytes() if bulk.exists() else None)
            if bulk.exists(): self.sources[package + '.ubulk'] = hashlib.sha256(bulk.read_bytes()).hexdigest()
        return self.images[package]

    def material_image(self, doc, ref):
        d = self.load(self.package(doc, ref)); f = fields(d['Exports'][0])
        params = f.get('TextureParameterValues', [])
        for name in ('Albedo', 'Diffuse', 'BaseColor', 'Base Color', 'Color', 'Basecolor_Base'):
            found = next((p for p in params if p['ParameterInfo']['Name'] == name), None)
            if found and found['ParameterValue'] < 0: return self.image(self.package(d, found['ParameterValue']))
        # Native materials also contain direct texture defaults in their imports.
        candidates = [i for i, v in enumerate(d['Imports']) if v['ClassName'] == 'Texture2D' and v['ObjectName'].endswith('_D')]
        if candidates: return self.image(self.package(d, -candidates[0]-1))
        if f.get('Parent', 0) < 0: return self.material_image(d, f['Parent'])
        return None


def build(args):
    assets = NativeAssets(args.content, args.cache, args.sdk, args.usmap)
    result = {'schema': 1, 'terrain': [], 'props': [], 'foliage': [], 'sources': {}, 'omitted': []}
    images = {}
    # The material's paint establishes paths/grass/rock boundaries. Diffuse
    # samples retain native surface detail with simplified, static lighting.
    layer_names = {'Grass': 'grass001', 'Grass_Y': 'grass001', 'Dirt': 'earthground001',
                   'Rock': 'Rock001', 'Beach': 'sand001', 'Forest': 'forest001'}
    layer_images = {}
    for key, name in layer_names.items():
        package = '/Game/Env/Wld/00Com/Textures/T_Env_Wld_00Com_' + name + '_D'
        try: layer_images[key] = np.asarray(assets.image(package).resize((256, 256)))[:, :, :3]
        except (FileNotFoundError, ValueError, KeyError): layer_images[key] = None
    colors = {'Grass': (96, 136, 62), 'Grass_Y': (136, 152, 58), 'Dirt': (174, 143, 93),
              'Rock': (128, 132, 122), 'Beach': (190, 179, 136), 'Forest': (63, 113, 58)}
    for source in args.landscape:
        document = json.loads(source.read_text(encoding='utf-8-sig'))
        assets.sources[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
        for index, e in enumerate(document['Exports'], 1):
            f = fields(e)
            if not f.get('WeightmapLayerAllocations'): continue
            transform = component_matrix(document, index)
            at = transform[:3, 3]; dx, dy = transform[0, 0], transform[1, 1]
            weights = [weightmap(document['Exports'][i-1]) for i in f['WeightmapTextures']]
            color = np.zeros((128, 128, 3), dtype=np.float64); total = np.zeros((128, 128))
            for layer in f['WeightmapLayerAllocations']:
                name = document['Imports'][-layer['LayerInfo']-1]['ObjectName'].split('_LayerInfo')[0]
                w = weights[layer['WeightmapTextureIndex']][:, :, layer['WeightmapTextureChannel']].astype(float)
                base = np.array(colors.get(name, (148, 137, 111)))
                tex = layer_images.get(name)
                if tex is not None:
                    xx, yy = np.meshgrid(np.arange(128)*dx+at[0], np.arange(128)*dy+at[1])
                    texel = tex[(yy*.5).astype(int)%256, (xx*.5).astype(int)%256].astype(float)
                    # Native grass is procedural/tinted; retain its paint rather
                    # than treating its untinted texture as final shader color.
                    base = base * (.75 + texel.mean(axis=2)[:, :, None] / 255 * .5)
                color += base * w[:, :, None]; total += w
            if np.any(total == 0): raise ValueError('Native paint has an unassigned texel.')
            rgb = np.clip(color / total[:, :, None], 0, 255).astype('uint8')
            name = f'terrain_{len(result["terrain"])}.png'; images[name] = Image.fromarray(rgb)
            result['terrain'].append({'x': float(at[0]), 'y': float(at[1]), 'image': name})
        for index, e in enumerate(document['Exports'], 1):
            if not e['ObjectName'].startswith('FoliageInstancedStaticMeshComponent'): continue
            f = fields(e); package = assets.package(document, f['StaticMesh'])
            if 'Billboard' not in package: continue
            try:
                d = assets.load(package); mf = fields(next(x for x in d['Exports'] if 'ExtendedBounds' in fields(x)))
                tex = assets.material_image(d, mf['StaticMaterials'][0]['MaterialInterface'])
                if tex is None: raise ValueError('No native foliage diffuse.')
                name = 'foliage_' + Path(package).name + '.png'; images[name] = tex.resize((256, 256))
                half = vector(mf['ExtendedBounds']['BoxExtent'])
                extension = vector(mf.get('PositiveBoundsExtension', dict(X=0, Y=0, Z=0)))
                # ExtendedBounds includes renderer padding, not sprite size.
                width = 2*max(half[0]-extension[0], half[1]-extension[1]); height = 2*(half[2]-extension[2])
                if width <= 0 or height <= 0: raise ValueError('Invalid foliage visible bounds.')
                parent = component_matrix(document, f['AttachParent'])
                for local in foliage_matrices(e):
                    m = parent @ local; p = m[:3, 3]; scale = np.linalg.norm(m[:3, :3], axis=0)
                    result['foliage'].append({'at': [round(float(v), 4) for v in p],
                                             'width': round(width*max(scale[:2]), 4), 'height': round(height*scale[2], 4), 'image': name})
            except (ValueError, FileNotFoundError, KeyError) as error: result['omitted'].append(package + ': ' + str(error))
    for source in args.world:
        document = json.loads(source.read_text(encoding='utf-8-sig'))
        assets.sources[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
        for index, e in enumerate(document['Exports'], 1):
            f = fields(e)
            if f.get('StaticMesh', 0) >= 0: continue
            owner = fields(document['Exports'][e['OuterIndex']-1]) if e.get('OuterIndex', 0) > 0 else {}
            if f.get('bVisible') is False or f.get('bHiddenInGame') or owner.get('bHidden'):
                continue
            package = assets.package(document, f['StaticMesh'])
            # These are shader-generated translucent shore/foam surfaces. An
            # opaque diffuse fallback would cover paths and scenery underneath.
            if 'foam' in package.lower():
                result['omitted'].append(package + ': translucent shader omitted'); continue
            try:
                d = assets.load(package); vertices, uvs, triangles = mesh(d)
                m = component_matrix(document, index)
                v = (m @ np.column_stack([vertices, np.ones(len(vertices))]).T).T[:, :3]
                mf = fields(next(x for x in d['Exports'] if 'ExtendedBounds' in fields(x)))
                materials = []
                for mat in mf['StaticMaterials']:
                    try: materials.append(assets.material_image(d, mat['MaterialInterface']))
                    except (ValueError, FileNotFoundError, KeyError) as error:
                        materials.append(None); result['omitted'].append(package + ' material: ' + str(error))
                faces = []
                for ids, material in triangles:
                    a, b, c = v[list(ids)]; normal = np.cross(b-a, c-a); length = np.linalg.norm(normal)
                    if length < 1e-8: continue
                    light = .55 + .45 * abs(np.dot(normal / length, [-.4, -.5, .75]))
                    color = (49, 109, 127) if any(n in package.lower() for n in ('water', 'river', 'ocean')) else (128, 136, 114)
                    tex = materials[material] if material < len(materials) else None
                    if tex is not None:
                        u, t = np.mean(np.array(uvs)[list(ids)], axis=0)
                        color = tex.getpixel((int(u%1*tex.width), int(t%1*tex.height)))[:3]
                    faces.append([list(ids), [int(min(255, max(0, n*light))) for n in color]])
                result['props'].append({'name': Path(package).name, 'vertices': np.round(v, 3).tolist(), 'faces': faces})
            except (ValueError, FileNotFoundError, KeyError) as error: result['omitted'].append(package + ': ' + str(error))
    result['sources'] = assets.sources
    result['omitted'] = sorted(set(result['omitted']))
    files = {}
    for name, image in images.items():
        out = io.BytesIO(); image.save(out, format='PNG', optimize=True); files[name] = out.getvalue()
    result['files'] = {n: hashlib.sha256(v).hexdigest() for n, v in files.items()}
    files['scene.json'] = (json.dumps(result, separators=(',', ':')) + '\n').encode()
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 4, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; z.writestr(info, data)
    args.output.with_suffix('.json').write_text(json.dumps({'schema': 1, 'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                                                          'sceneSha256': hashlib.sha256(files['scene.json']).hexdigest()}) + '\n', encoding='utf-8')
    print(f'Native scenery: {len(result["terrain"])} painted patches, {len(result["props"])} meshes, {len(result["foliage"])} foliage instances; {len(result["omitted"])} omitted dependencies.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--content', type=Path, action='append', required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--sdk', nargs='+', required=True)
    p.add_argument('--usmap', type=Path, required=True)
    p.add_argument('--landscape', type=Path, action='append', required=True)
    p.add_argument('--world', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, default=Path('assets/acquisition_map/scenery.zip'))
    build(p.parse_args())
