"""Render Studio previews from native body pixels and the supplied crystal mesh.

This software renderer previews geometry/motion, not Unreal's glass shader.
It never writes game assets or repaints the supplied sprite pixels.
"""
import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'assets/existing_visions/payload'))
import _ffr_crystal_cave as cave
from _ffr_crystal_mesh import lod0_geometry
import _ffr_fina_motion as motion


def geometry(view):
    """Read the checked inline LOD0; leave all native render/bulk bytes alone."""
    _, mesh = cave.export(view, 'SM_Env_Com_crystal008')
    positions, indices = lod0_geometry(base64.b64decode(mesh['Extras'], validate=True))
    origin = cave.property_data(cave.property_data(mesh, 'ExtendedBounds'), 'Origin')['Value'][0]['Value']
    ratio = cave.TEST_CRYSTAL_SCALE / cave.TEST_SPRITE_SCALE
    return [[(p[i] - float(origin[axis])) * ratio for i, axis in enumerate(('X', 'Y', 'Z'))] for p in positions], indices


def current(keys, tick): return next(value for time, value in reversed(keys) if time <= tick)


def render(atlas, spec, vertices, indices, name, length, step):
    clip = next(a for a in spec['animations'] if a['name'] == name); parts = clip['parts']; cells = {}
    for cell in spec['cells']:
        x, y = map(int, cell['pos']); w, h = map(int, cell['size'])
        cells[cell['name']] = (atlas.crop((x, y, x + w, y + h)), cell['pivot'])
    factor, origin_x, floor_y = 2.2, 140, 326
    frames, durations = [], []
    for tick in range(0, length, step):
        t = min(tick, clip['frameCount'] - 1); image = Image.new('RGBA', (280, 360))
        casing = parts['NULL_Crystal']; center = current(casing['Posy'], t)
        angle = math.radians(current(casing['Roty'], t)); cosine, sine = math.cos(angle), math.sin(angle)
        points = [(x * cosine - y * sine, x * sine + y * cosine, z) for x, y, z in vertices]
        faces = []
        if center > -100:
            for tri in indices:
                a, b, c = (points[i] for i in tri)
                u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                size = math.sqrt(sum(n * n for n in normal)) or 1
                brightness = abs(sum(normal[i] * (0.3, -0.7, 0.6)[i] for i in range(3))) / size
                depth = sum(p[1] for p in (a, b, c)) / 3
                polygon = [(origin_x + p[0] * factor, floor_y - (center + p[2]) * factor) for p in (a, b, c)]
                faces.append((depth, polygon, brightness))
        def glass(front):
            layer = Image.new('RGBA', image.size); draw = ImageDraw.Draw(layer)
            for depth, polygon, bright in sorted(faces, reverse=True):
                if (depth <= 0) != front: continue
                draw.polygon(polygon, fill=(round(70 + 60 * bright), round(160 + 70 * bright), 245, 42 if front else 22))
            if front:
                mask = layer.getchannel('A').point(lambda a: 255 if a else 0)
                edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)), mask.filter(ImageFilter.MinFilter(3)))
                rim = Image.new('RGBA', image.size, (175, 225, 255, 0)); rim.putalpha(edge.point(lambda a: round(a * .18)))
                layer.alpha_composite(rim)
            image.alpha_composite(layer)
        glass(False)
        body = parts['part_0']; cell, pivot = cells[current(body['Cell'], t)]
        scaled = cell.resize((round(cell.width * factor), round(cell.height * factor)), Image.Resampling.NEAREST)
        x, y = current(body['Posx'], t), current(body['Posy'], t)
        if current(body.get('Imgfliph', [[0, 0.0]]), t): scaled = scaled.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        location = (round(origin_x + x * factor - (.5 + pivot[0]) * scaled.width),
                    round(floor_y - y * factor - (.5 - pivot[1]) * scaled.height))
        strength = 0
        if name == 'LB1':
            for begin, full, fade, end in motion.FLASHES:
                if begin <= tick < end:
                    strength = ((tick - begin) / (full - begin) if tick < full
                                else 1 if tick <= fade else (end - tick) / (end - fade))
                    break
        if strength:
            glow = Image.new('RGBA', image.size); glow.paste((255, 218, 75, 0), (0, 0, *image.size))
            alpha = Image.new('L', image.size); alpha.paste(scaled.getchannel('A'), location)
            alpha = alpha.filter(ImageFilter.GaussianBlur(8)).point(lambda a: round(a * .75 * strength))
            glow.putalpha(alpha); image.alpha_composite(glow)
        image.alpha_composite(scaled, location); glass(True)
        frames.append(image)
        durations.append(round(min(tick + step, length) * 1000 / 60) - round(tick * 1000 / 60))
    output = io.BytesIO()
    frames[0].save(output, format='WEBP', save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, lossless=True, method=4, minimize_size=False)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project-json', 'texture-json', 'mesh-json', 'old-sheet', 'original-spec', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    original = load(args.original_spec)
    atlas, spec = motion.battle_spec(load(args.project_json), load(args.texture_json), args.old_sheet, original)
    vertices, indices = geometry(load(args.mesh_json)); files, animations = {}, {}
    lengths = {a['name']: a['frameCount'] for a in spec['animations']}
    for public, native, length, step in [('idle', 'idle', 6000, 15), ('atk', 'Studio_FinaCast', lengths['Studio_FinaCast'], 1), ('limitatk', 'LB1', lengths['LB1'], 2)]:
        data = render(atlas, spec, vertices, indices, native, length, step)
        name = public + '.webp'; files[name] = data
        animations[public] = {'file': name, 'seconds': length / 60, 'sha256': hashlib.sha256(data).hexdigest()}
        print(public, len(data), 'bytes', flush=True)
    manifest = {'schema': 1, 'presentation': 'native-fina-8', 'description': 'Native battle preview; game lighting and refraction may differ.',
                'animations': animations, 'sources': {name: hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()
                    for name in ('project_json', 'texture_json', 'mesh_json', 'old_sheet', 'original_spec')}}
    files['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


if __name__ == '__main__': main()
