"""Render non-installing previews of the shared native Fina battle motions."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "assets/existing_visions/payload"))
from _ffr_fina_motion import *

def preview(view, texture, old_sheet, result, destination):
    """Render source pixels at their authored pivots; crystal/FX are separate."""
    from PIL import Image, ImageDraw
    atlas = extract_atlas(texture)
    cells = {}
    for cell in prop(prop(native_project(view), 'CellmapList')[0], 'Cells'):
        pos, size, pivot = (vector(cell, n) for n in ('Pos', 'Size', 'Pivot'))
        x, y, w, h = (int(float(v)) for v in (pos['X'], pos['Y'], size['X'], size['Y']))
        if not (0 <= x < x + w <= atlas.width and 0 <= y < y + h <= atlas.height):
            raise ValueError('Native cell lies outside its atlas.')
        cells[prop(cell, 'CellName')] = (atlas.crop((x, y, x + w, y + h)), pivot)
    # Original frame 174 is the jacket-free seated hold (111 frames) in the
    # supplied custom animation. Crop only transparent padding; keep its pixels.
    original = Image.open(old_sheet).convert('RGBA')
    if original.size != (1800, 1820): raise ValueError('The original Fina sheet changed.')
    seat = original.crop((9 * 120, 11 * 130, 10 * 120, 12 * 130))
    bounds = seat.getbbox()
    if not bounds: raise ValueError('The original seated sprite is blank.')
    left, top, right, bottom = bounds
    cell = seat.crop(bounds)
    cells['original_jacket_free_seated'] = (cell, {
        'X': (60 - left) / cell.width - .5, 'Y': .5 - (100 - top) / cell.height})
    def current(keys, frame): return next(v for t, v in reversed(keys) if t <= frame)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('attack', 'resonance'):
        clip = result[name]; body = clip['parts']['part_0']; frames = []
        for frame in range(clip['frameCount']):
            cell, pivot = cells[current(body['Cell'], frame)]
            image = Image.new('RGBA', (320, 500), '#203044')
            draw = ImageDraw.Draw(image)
            draw.text((12, 12), name.title() + ' - body motion draft', fill='white')
            draw.text((12, 28), 'Crystal / glow / blast not shown', fill='#cad5e0')
            draw.line((20, 468, 300, 468), fill='#65788c')
            x = current(body['Posx'], frame); y = current(body['Posy'], frame)
            scaled = cell.resize((cell.width * 3, cell.height * 3), Image.Resampling.NEAREST)
            location = (round(160 + x * 3 - (.5 + float(pivot['X'])) * scaled.width),
                        round(468 - y * 3 - (.5 - float(pivot['Y'])) * scaled.height))
            image.alpha_composite(scaled, location)
            frames.append(image.convert('RGB'))
        durations = [20 if i % 3 != 1 else 10 for i in range(len(frames))]
        frames[0].save(destination / (name + '-body-draft.gif'), save_all=True, append_images=frames[1:],
                       duration=durations, loop=0, disposal=2)
    return cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_json', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--texture-json', type=Path)
    parser.add_argument('--old-sheet', type=Path)
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    result = draft(json.loads(args.project_json.read_text(encoding='utf-8-sig')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Wrote body-only animation draft:', args.output)
    if args.preview_dir:
        if not args.texture_json or not args.old_sheet:
            parser.error('--preview-dir requires --texture-json and --old-sheet')
        preview(json.loads(args.project_json.read_text(encoding='utf-8-sig')),
                json.loads(args.texture_json.read_text(encoding='utf-8-sig')), args.old_sheet, result, args.preview_dir)


if __name__ == '__main__': main()
