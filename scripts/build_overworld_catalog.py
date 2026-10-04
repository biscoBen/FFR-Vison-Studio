"""Audit a pinned FFBE dump and build the genuine directional field catalog.

Inputs: town/, unit_icons/, root-tree.json, town-tree.json, unit_icons-tree.json,
and unit_animated_csv-tree.json from the same GitHub snapshot. No network work.
Unknown/new town sheets must be reviewed rather than silently omitted or guessed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MODELS = (
    ('rain', 'Rain', '100000102', '100000106', 'map_character1.png'),
    ('lasswell', 'Lasswell', '100000202', '100000206', 'map_character2.png'),
    ('fina', 'Fina', '100000302', '100000306', 'map_character3.png'),
    ('nichol', 'Nichol', '100000403', '100000406', 'map_character4.png'),
    ('lid', 'Lid', '100000503', '100000506', 'map_character5.png'),
    ('jake', 'Jake', '100000703', '100000706', 'map_character7.png'),
    ('vagrant_knight_rain', 'Vagrant Knight Rain', '100015005', '100015006', 'map_character11.png'),
    ('pyro_glacial_lasswell', 'Pyro Glacial Lasswell', '100011705', '100011706', 'map_character12.png'),
    ('unidentified_cloaked_field', 'Unidentified cloaked character', None, None, 'map_character99.png'),
)
DIRECTIONS = ((2, 0), (8, 1), (4, 2), (6, 3), (1, 4), (3, 5), (7, 6), (9, 7))


def sha(data): return hashlib.sha256(data).hexdigest()


def cell(image, row, col):
    return image.crop((col * 64, row * 64, (col + 1) * 64, (row + 1) * 64))


def has_character(image):
    # Empty directional slots often retain an opaque dark oval shadow. Alpha
    # bounds alone would incorrectly advertise that shadow as a usable sprite.
    pixels = image.convert('RGBA').tobytes()
    return sum(1 for red, green, blue, alpha in zip(pixels[0::4], pixels[1::4], pixels[2::4], pixels[3::4])
               if alpha > 64 and max(red, green, blue) > 65) > 15


def audit(image):
    if image.width != 448 or image.height not in (1536, 1600):
        raise ValueError('Unreviewed field sheet layout: ' + str(image.size))
    motions = {}
    removed = {}
    for direction, row in DIRECTIONS:
        idle = cell(image, row, 0)
        if has_character(idle): motions[f'idle{direction}'] = [[row, 0]]
        standing = {cell(image, row, col).tobytes() for col in range(7)
                    if has_character(cell(image, row, col))}
        for motion, offset in (('move', 16), ('dash', 8)):
            # Column zero is the layout's rest pose. Also remove identical idle
            # poses anywhere else in the loop, rather than assuming only col 0.
            frames = [[row + offset, col] for col in range(1, 7)
                      if has_character(cell(image, row + offset, col))
                      and cell(image, row + offset, col).tobytes() not in standing]
            if len({cell(image, r, c).tobytes() for r, c in frames}) >= 2:
                motions[f'{motion}{direction}'] = frames
            removed[f'{motion}{direction}'] = [col for col in range(7)
                                                if [row + offset, col] not in frames]
    if any(f'{motion}{direction}' not in motions
           for direction in (2, 8, 4, 6) for motion in ('idle', 'dash')):
        return None, removed
    count = 8 if all(f'dash{direction}' in motions for direction, _ in DIRECTIONS) else 4
    native = set(motions)
    fallbacks = {}
    for direction, _ in DIRECTIONS:
        cardinal = 2 if direction in (1, 3) else 8 if direction in (7, 9) else direction
        for motion in ('idle', 'move', 'dash'):
            key = f'{motion}{direction}'
            if key in motions: continue
            # Preserve genuine diagonal run art at walking speed when the
            # separate walk block is empty; 4-way models use their own cardinals.
            donor = f'dash{direction}' if motion == 'move' and f'dash{direction}' in motions else f'{motion}{cardinal}'
            if donor not in motions and motion == 'move': donor = f'dash{cardinal}'
            if donor not in motions: raise ValueError('No drawable donor for ' + key)
            motions[key] = motions[donor]
            fallbacks[key] = donor
    return {'directions': count, 'motions': motions, 'native_motions': sorted(native), 'fallbacks': fallbacks}, removed


def build(source):
    source = Path(source)
    root = json.loads((source / 'root-tree.json').read_text())
    trees = {folder: json.loads((source / (folder + '-tree.json')).read_text())
             for folder in ('town', 'unit_icons', 'unit_animated_csv')}
    for folder, tree in trees.items():
        expected = next(x['sha'] for x in root['tree'] if x['path'] == folder)
        if tree['sha'] != expected or tree['truncated']:
            raise ValueError('Incomplete or mixed source tree: ' + folder)
    blobs = {folder: {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
             for folder, tree in trees.items()}
    def verified(folder, name):
        data = (source / folder / name).read_bytes()
        git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if git_sha != blobs[folder][name]['sha']: raise ValueError('Source blob changed: ' + name)
        return data
    expected_sheets = {x[-1] for x in MODELS} | {'map_character6.png', 'map_characteqr7.png'}
    actual_sheets = {name for name in blobs['town'] if name.startswith(('map_character', 'map_characteqr'))}
    if actual_sheets != expected_sheets: raise ValueError('Review new/missing town sheets: ' + str(actual_sheets ^ expected_sheets))
    if verified('town', 'map_characteqr7.png') != verified('town', 'map_character1.png'):
        raise ValueError('Previously duplicate Rain sheet now differs.')
    with Image.open(source / 'town/map_character6.png') as image:
        if audit(image.convert('RGBA'))[0] is not None:
            raise ValueError('Sakura now has a usable run; review her for inclusion.')
    archive_files = {}
    models = {}
    report = {}
    for model, name, base, form, sheet in MODELS:
        data = verified('town', sheet)
        with Image.open(source / 'town' / sheet) as raw: image = raw.convert('RGBA')
        audited, removed = audit(image)
        if not audited: raise ValueError('No usable cardinal run: ' + sheet)
        icon = 'unit_icon_' + form + '.png' if form else 'unidentified_cloaked_field.png'
        archive_files[sheet] = data
        if form: archive_files[icon] = verified('unit_icons', icon)
        else:
            import io
            buffer = io.BytesIO(); cell(image, 0, 0).save(buffer, format='PNG'); archive_files[icon] = buffer.getvalue()
        models[model] = dict(name=name, base=base, form=form or model, icon=icon, sheet=sheet,
                             size=list(image.size), sheet_sha256=sha(data), icon_sha256=sha(archive_files[icon]), **audited)
        report[model] = {'directions': audited['directions'], 'removed_columns': removed,
                         'fallbacks': audited['fallbacks']}
    payload = ROOT / 'assets/existing_visions/payload'
    archive = payload / 'overworld_assets.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name, data in sorted(archive_files.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); entry.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(entry, data)
    value = {'schema': 1, 'source': {'repository': 'DaddyRaegen/ffbe_asset_dump', 'commit': root['sha'],
             'town_blobs_audited': len(blobs['town']), 'unit_animation_csv_blobs_audited': len(blobs['unit_animated_csv'])},
             'archive': archive.name, 'archive_sha256': sha(archive.read_bytes()), 'models': models}
    (payload / 'overworld_catalog.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    # CharacterConfig validates synchronously, so its allowlist and selector data
    # are generated from exactly the same audited catalog as the Python importer.
    dart = '// Generated by scripts/build_overworld_catalog.py; do not edit.\n'
    dart += 'const overworldCatalog = <String, dynamic>' + json.dumps(value, ensure_ascii=False, indent=2) + ';\n'
    (ROOT / 'lib/services/overworld_catalog.dart').write_text(dart)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--source', required=True)
    report = build(parser.parse_args().source)
    print(json.dumps(report, indent=2))
