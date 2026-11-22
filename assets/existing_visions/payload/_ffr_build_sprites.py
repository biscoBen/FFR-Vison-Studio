"""Run the compatible engine sprite converter with recovered motion aliases."""
from pathlib import Path
import json
import runpy
import sys
from PIL import Image, ImageOps

tools = Path(__file__).parent
sys.path.insert(0, str(tools / 'ffbe2ss6'))
sys.path.insert(0, str(tools))
import ffbe_frames
import _ffr_animation_repair
import _ffr_ability_modes
_ffr_animation_repair.extend_frames(ffbe_frames)
converter = runpy.run_path(str(tools / 'ffbe2ss6/build_sprites.py'))
sheets = converter['Sheets']


def steps_for(self, spec):
    out = []
    aliases = {'atk1': 'atk', 'atk2': 'atk', 'atk3': 'atk'}
    for name in spec.split('+'):
        found = None
        for key in self.src:
            for candidate in dict.fromkeys((name, aliases.get(name, name))):
                if self.anims(key).get(candidate):
                    found = [dict(s, src=key) for s in self.anims(key)[candidate]]; break
            if found: break
        if not found and name == 'standby':
            found = [dict(s, src='a') for s in self.anims('a').get('idle', [])]
        if found: out.extend(found)
    return out or [dict(s, src='a') for s in self.anims('a').get('idle', [])]


sheets.steps_for = steps_for
motions = converter['BATTLE_ANIMS']
motions[:] = [(name, {'attack_B': 'atk2', 'attack_C': 'atk3'}.get(name, motion)) for name, motion in motions]


def locked_menu(atlas, spec, pack, max_w):
    """Give only the menu Lock clip dark grey copies of its own source cells.

    The native vision list chooses Lock while a vision is unowned. Imported
    menus used the same full-colour cells for Lock and the ordinary poses.
    Baking private cells avoids changing the shared texture or relying on
    PartsColor attributes unsupported by the pinned native writer.
    """
    locked, = [clip for clip in spec['animations'] if clip['name'] == 'Lock']
    references = [key for part in locked['parts'].values() for key in part.get('Cell', [])]
    if not references:
        raise ValueError('The imported menu Lock animation has no sprite cells.')
    images = {}
    cells = {cell['name']: cell for cell in spec['cells']}
    for name, cell in cells.items():
        x, y = cell['pos']; w, h = cell['size']
        images[name] = atlas.crop((int(x), int(y), int(x + w), int(y + h)))
    replacements = {}
    for _, name in references:
        if name in replacements:
            continue
        replacement = name + '_locked'
        if replacement in cells:
            raise ValueError('Duplicate locked menu sprite cell: ' + replacement)
        source = images[name]
        grey = ImageOps.grayscale(source).point(lambda value: round(value * .4))
        images[replacement] = Image.merge('RGBA', (grey, grey, grey, source.getchannel('A')))
        spec['cells'].append(dict(cells[name], name=replacement))
        replacements[name] = replacement
    (width, height), positions = pack(images, max_w)
    result = Image.new('RGBA', (width, height))
    for cell in spec['cells']:
        name = cell['name']
        result.paste(images[name], positions[name])
        cell['pos'] = [float(n) for n in positions[name]]
    spec['pixelSize'] = [float(width), float(height)]
    for key in references:
        key[1] = replacements[key[1]]
    return result, spec


original_build = converter['build']


def build(sheets, animations, prefix, max_w):
    atlas, spec = original_build(sheets, animations, prefix, max_w)
    if animations is converter['MENU_ANIMS']:
        atlas, spec = locked_menu(atlas, spec, converter['pack'], max_w)
    return atlas, spec


# runpy returns a copy of the module dictionary. Bind the function in main's
# actual globals so the existing CLI writes the new spec, PNG and BGRA together.
converter['main'].__globals__['build'] = build
converter['main']()
trial = tools.parent / 'build/barrage-trial.json'
spec_file = Path(sys.argv[4]) / 'battle/spec.json'
if spec_file.is_file() and '--menu-only' not in sys.argv:
    spec = json.loads(spec_file.read_bytes())
    aliases = _ffr_animation_repair.native_caster_motions(spec, _ffr_ability_modes.settings(tools.parent))
    roster = tools.parent / 'mods/EstherTsukiko/units.json'
    if roster.is_file():
        import _ffr_shrine_challenges as challenges
        import _ffr_sephira
        saved_units = json.loads(roster.read_bytes())
        if (_ffr_sephira.native_motion_for(saved_units, sys.argv[3])
                or challenges.enemy_motion_for(saved_units, sys.argv[3])):
            selected = next((u for u in saved_units if str(u.get('id')) == sys.argv[3]), None)
            required = _ffr_sephira.native_motion_names(selected) if selected else []
            aliases.extend(_ffr_animation_repair.native_caster_motions(spec,
                {'showUnverified': True, 'useChanges': False, 'useNativeRepairs': True}, required))
    if aliases: print('  Native caster motions use this character\'s own clips: ' + ', '.join(aliases) + '; original skill effects retained.')
    if trial.is_file():
        _ffr_animation_repair.add_barrage_animation(spec, json.loads(trial.read_bytes()), sys.argv[3])
    if aliases or trial.is_file(): spec_file.write_text(json.dumps(spec, indent=1), encoding='utf-8')
