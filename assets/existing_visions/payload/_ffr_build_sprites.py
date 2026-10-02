"""Run the compatible engine sprite converter with recovered motion aliases."""
from pathlib import Path
import json
import runpy
import sys

tools = Path(__file__).parent
sys.path.insert(0, str(tools / 'ffbe2ss6'))
sys.path.insert(0, str(tools))
import ffbe_frames
import _ffr_animation_repair
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
converter['main']()
trial = tools.parent / 'build/barrage-trial.json'
spec_file = Path(sys.argv[4]) / 'battle/spec.json'
if trial.is_file() and spec_file.is_file() and '--menu-only' not in sys.argv:
    spec = json.loads(spec_file.read_bytes())
    _ffr_animation_repair.add_barrage_animation(spec, json.loads(trial.read_bytes()), sys.argv[3])
    spec_file.write_text(json.dumps(spec, indent=1), encoding='utf-8')
