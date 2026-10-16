"""Compose imported portraits inside native Resonance frames, without FFBE badges."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageChops


def render(kind, icon, size, donors, layout=None):
    """Keep native frame pixels outside its supplied portrait-replacement mask."""
    with Image.open(Path(donors) / f'{kind}_13110.png') as image:
        frame = image.convert('RGBA')
    with Image.open(Path(donors) / f'{kind}_mask.png') as image:
        mask = image.convert('L').point(lambda n: 255 if n else 0)
    if frame.size != (size, size) or mask.size != frame.size or mask.getbbox() is None:
        raise ValueError('The native vision icon frame/mask dimensions changed.')
    x0, y0, x1, y1 = mask.getbbox()
    # Remove the donor's portrait and leave the native frame/ornament intact.
    frame.paste((0, 0, 0, 0), (0, 0), mask)
    values = (layout or {}).get(kind) or {}
    scale, dx, dy = (float(values.get(k, d)) for k, d in
                     (('iconScale', 1), ('iconX', 0), ('iconY', 0)))
    if not all(math.isfinite(n) for n in (scale, dx, dy)) or not 0 < scale <= 20:
        raise ValueError('Invalid portrait scale or position in icon layout.')
    src = icon.convert('RGBA')
    factor = (x1 - x0 - 2) / src.width * scale
    width, height = max(1, round(src.width * factor)), max(1, round(src.height * factor))
    src = src.resize((width, height), Image.Resampling.NEAREST)
    left = round((x0 + x1 - width) / 2 + dx * size)
    top = round((y0 + y1 - height) / 2 + dy * size)
    layer = Image.new('RGBA', frame.size)
    layer.alpha_composite(src, (left, top))
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), mask))
    frame.alpha_composite(layer)
    return frame


def install_preview(env):
    module = env.get('build_icons')
    if module is None: return
    donors = Path(env['ROOT']) / 'build/icons/donors'
    def preview(kind, icon, size, style='border', rarity='7', layout=None):
        return render(kind, icon, size, donors, layout)
    module.render = preview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory'); parser.add_argument('form'); parser.add_argument('output')
    # Read old saved style/rarity arguments without changing the saved config.
    parser.add_argument('--style'); parser.add_argument('--rarity'); parser.add_argument('--layout')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    layout = json.loads(Path(args.layout).read_text(encoding='utf-8-sig')) if args.layout else None
    with Image.open(Path(args.directory) / f'unit_icon_{args.form}.png') as icon:
        for kind, size in (('face', 128), ('timeline', 128), ('ability', 64)):
            image = render(kind, icon, size, root / 'build/icons/donors', layout)
            image.save(output / (kind + '.png'))
            (output / (kind + '.bgra')).write_bytes(image.tobytes('raw', 'BGRA'))
            print(kind, image.size, 'native Resonance frame (no FFBE badge)')


if __name__ == '__main__': main()
