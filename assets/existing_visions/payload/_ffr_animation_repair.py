"""Recover matching FFBE motions and author missing, motion-only battle timelines.

Original skill mechanics and existing sequences are never replaced. The asset
dump provides unit motions, not the missing spell/ability particle effects.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import threading
import tempfile
import urllib.request

ALIASES = {'magicatk': 'magic_atk', 'limitatk': 'limit_atk', 'winbefore': 'win_before'}
_index = None
_attempted = set()
_lock = threading.RLock()


def index():
    global _index
    if _index is None:
        _index = json.loads(Path(__file__).with_name('ffbe_animation_index.json').read_bytes())
        if (_index.get('schema') != 1 or _index.get('repository') != 'DaddyRaegen/ffbe_asset_dump'
                or not re.fullmatch(r'[0-9a-f]{40}', _index.get('commit', ''))):
            raise ValueError('Invalid bundled FFBE animation index.')
    return _index


def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def fetch(path, digest, source, maximum=32 * 1024 * 1024):
    if not re.fullmatch(r'(unit_animated|unit_animated_csv)/unit_[A-Za-z0-9_]+\.(png|csv)', path):
        raise ValueError('Invalid FFBE asset path.')
    url = f'https://raw.githubusercontent.com/{source["repository"]}/{source["commit"]}/{path}'
    with urllib.request.urlopen(url, timeout=12) as response:
        data = response.read(maximum + 1)
    if len(data) > maximum or blob_sha(data) != digest:
        raise ValueError('FFBE animation download checksum mismatch.')
    return data


def csv_rows(data, keep_empty=False):
    return [row for row in csv.reader(io.StringIO(data.decode('utf-8-sig'))) if keep_empty or row]


def repair_form(folder, form, source=None, download=fetch):
    """Fill absent motions only when the atlas and frame definitions match.

    Existing files (including hand-edited sprites) are retained. A connection
    failure leaves the previous usable pack intact and does not block a build.
    """
    form = str(form); folder = Path(folder)
    if not form.isdigit() or not folder.is_dir(): return []
    source = source or index(); entry = source['forms'].get(form)
    if not entry: return []
    atlas = folder / f'unit_anime_{form}.png'; cgg = folder / f'unit_cgg_{form}.csv'
    if not atlas.is_file() or not cgg.is_file(): return []
    missing = {}
    reverse = {v: k for k, v in ALIASES.items()}
    for motion, digest in entry.items():
        if motion in ('atlas', 'cgg'): continue
        names = {motion, ALIASES.get(motion, motion), reverse.get(motion, motion)}
        if not any((folder / f'unit_{name}_cgs_{form}.csv').exists() for name in names):
            missing[motion] = digest
    if not missing: return []
    key = (str(folder.resolve()), form, atlas.stat().st_mtime_ns, cgg.stat().st_mtime_ns)
    with _lock:
        if key in _attempted: return []
        _attempted.add(key)
        recovered = []
        try:
            local_cgg = cgg.read_bytes(); local_atlas = atlas.read_bytes()
            if blob_sha(local_cgg) != entry['cgg']:
                remote = download(f'unit_animated_csv/unit_cgg_{form}.csv', entry['cgg'], source)
                if csv_rows(remote, keep_empty=True) != csv_rows(local_cgg, keep_empty=True):
                    print(f'  FFBE motion repair: keeping edited/different frame data for {form}.'); return []
            if blob_sha(local_atlas) != entry['atlas']:
                remote = download(f'unit_animated/unit_anime_{form}.png', entry['atlas'], source)
                from PIL import Image
                with Image.open(io.BytesIO(remote)) as a, Image.open(io.BytesIO(local_atlas)) as b:
                    if a.size != b.size or a.convert('RGBA').tobytes() != b.convert('RGBA').tobytes():
                        print(f'  FFBE motion repair: keeping edited/different sprite sheet for {form}.'); return []
            frame_count = len(csv_rows(local_cgg, keep_empty=True))
            for motion, digest in missing.items():
                data = download(f'unit_animated_csv/unit_{motion}_cgs_{form}.csv', digest, source)
                steps = csv_rows(data)
                if not steps or any(len(s) < 4 or not 0 <= int(s[0]) < frame_count or int(s[3]) < 0 for s in steps):
                    raise ValueError('Recovered motion references invalid frames.')
                target = folder / f'unit_{motion}_cgs_{form}.csv'
                fd, temporary = tempfile.mkstemp(prefix='.ffbe-motion-', dir=folder)
                try:
                    with os.fdopen(fd, 'wb') as f:
                        f.write(data); f.flush(); os.fsync(f.fileno())
                    try: os.link(temporary, target) # Publish complete data without replacing a concurrent edit.
                    except FileExistsError: continue
                finally: Path(temporary).unlink(missing_ok=True)
                recovered.append(motion)
            if recovered: print(f'  FFBE motion repair: {form}: ' + ', '.join(recovered))
            return recovered
        except (OSError, ValueError) as error:
            print(f'  FFBE motion repair unavailable for {form}: {error}. Keeping existing assets.')
            return recovered


def repair_unit(unit, root):
    ff = unit.get('ffbe') or {}
    root = Path(root).resolve()
    for directory, form in ((ff.get('dir'), ff.get('id')), (ff.get('baseDir'), ff.get('baseForm'))):
        if not directory or not form: continue
        folder = (root / directory).resolve()
        if not folder.is_relative_to(root): raise ValueError('Sprite path escapes the engine.')
        repair_form(folder, form)


def extend_frames(module):
    """The converter previously read atk1 but only played atk, falling to idle."""
    original = module.load_unit
    def load(folder, form):
        atlas, cgg, motions = original(folder, form)
        for name in ('atk1', 'atk2', 'atk3', 'attack', 'magicstandby', 'jamp', 'before_win'):
            path = Path(folder) / f'unit_{name}_cgs_{form}.csv'
            if name not in motions and path.is_file(): motions[name] = module.read_cgs(path)
        for target, choices in {'atk': ('atk1', 'attack', 'atk2', 'atk3'), 'magic_standby': ('magicstandby',),
                                'jump': ('jamp',), 'winbefore': ('before_win',)}.items():
            if not motions.get(target):
                chosen = next((motions[n] for n in choices if motions.get(n)), None)
                if chosen: motions[target] = chosen
        return atlas, cgg, motions
    module.load_unit = load


def install_preview_hooks(env):
    catalog = env.get('ffbe_catalog'); downloads = env.get('unit_downloads')
    if catalog is None or downloads is None: return
    import ffbe_frames
    extend_frames(ffbe_frames)
    original_cgs = catalog.cgs_file
    def cgs(folder, form, motion):
        path = original_cgs(folder, form, motion)
        if path: return path
        for name in {'atk': ('atk1', 'attack'), 'magic_standby': ('magicstandby',),
                     'jump': ('jamp',), 'winbefore': ('before_win',)}.get(motion, ()):
            path = Path(folder) / f'unit_{name}_cgs_{form}.csv'
            if path.is_file(): return str(path)
        return None
    catalog.cgs_file = cgs
    original = downloads.ensure_selection
    def ensure(uid, form, report=lambda **kw: None):
        result = original(uid, form, report)
        folder = catalog.sprite_dir(str(form))
        recovered = repair_form(folder, form) if folder else []
        shift = catalog.shift_info(str(form))
        if shift:
            folder = catalog.sprite_dir(str(shift['base']))
            if folder: repair_form(folder, shift['base'])
        if recovered:
            for ext in ('webp', 'png'):
                for path in (Path(env['ROOT']) / 'build/devui/preview').glob(f'{form}_*.{ext}'):
                    path.unlink() # Derived previews only; original/user-authored sprites are retained.
        return result
    downloads.ensure_selection = ensure


def sequence_present(sid, rows, tables):
    rel = 'Asset/Skill/DT_SkillAsset'
    ids = {v['ID'] for v in rows(rel).values()}
    ids.update(r['set']['ID'] for r in tables.get(rel, {}).get('add', []) if 'ID' in r.get('set', {}))
    return any(sid + off in ids for off in (0, 1, 2))


def motion_seconds(unit, root, magic):
    ff = unit.get('ffbe') or {}; motion = 'magicatk' if magic else 'atk'
    for directory, form in ((ff.get('dir'), ff.get('id')), (ff.get('baseDir'), ff.get('baseForm'))):
        if not directory or not form: continue
        for name in (motion, ALIASES.get(motion, motion), *(() if magic else ('atk1', 'attack'))):
            p = Path(root) / directory / f'unit_{name}_cgs_{form}.csv'
            if p.is_file():
                return max(0.1, sum(max(1, int(s[3])) for s in csv_rows(p.read_bytes()) if len(s) >= 4) / 60)
    return 1.0


def prepare_sequences(tables, clones, jobs, units, root, rows, extract):
    """Add selected missing skill timelines; leave existing game rows untouched."""
    skill_rows = rows('Skill/DT_SkillData'); by_id = {r['ID']: r for r in skill_rows.values()}
    selected = {}
    for unit in units:
        for tier in [*unit.get('awakening', []), *unit.get('synchro', [])]:
            for grant in tier:
                if grant[0] == 'ActiveSkill': selected.setdefault(int(grant[1]), []).append(unit)
    repaired = []
    for sid, owners in sorted(selected.items()):
        if sequence_present(sid, rows, tables): continue
        recipes = [(u.get('skills') or {}).get(str(sid)) for u in owners]
        recipe = next((r for r in recipes if r), None)
        base = by_id.get(recipe['from'] if recipe else sid)
        if not base: continue
        skill = {**base, **((recipe or {}).get('set') or {})}
        if skill.get('skillAttrType', '').split('::')[-1] not in ('Ability', 'Magic', 'MagicSword', 'Fight'): continue
        magic = skill.get('skillAttrType', '').split('::')[-1] in ('Magic', 'MagicSword') or skill.get('DamageType', '').split('::')[-1] != 'Physic'
        hits = int(skill.get('hitCount') or 1)
        if not 0 < hits <= 30: continue
        import ffbe_resonance
        source = Path(root) / 'extracted/legacy' / (ffbe_resonance.SHELL + '.uasset')
        if not source.is_file(): extract('Sequencer/Battle/Skill/440110/440111/')
        if not source.is_file(): raise ValueError('The battle timeline template could not be extracted. Prepare the game files again.')
        plan = ffbe_resonance.schedule(max(motion_seconds(u, root, magic) for u in owners), hits, sid, movement={'enabled': False})
        plan['events'] = [e for e in plan['events'] if e['set']['EventType'] not in
                          ('PostSetDefaultColorGrading', 'PostSetColorGradingGlobalParameter', 'CameraSetDefault', 'OtherSetGameSpeed')]
        for event in plan['events']:
            st = event['set']
            if st.get('Unit_PlayAnimByName_AnimationName') == 'LB1': st['Unit_PlayAnimByName_AnimationName'] = 'magic_attack' if magic else 'attack_A'
            elif st.get('Unit_PlayAnimByName_AnimationName') == 'LB1_before': st['Unit_PlayAnimByName_AnimationName'] = 'magic_idle' if magic else 'command'
        asset = f'FFRS/Content/Sequencer/Battle/Skill/{sid}/{sid+1}/SEQ_Battle_{sid+1}_Master'
        clones.append({'from': ffbe_resonance.SHELL, 'to': asset,
                       'rename': [['SEQ_Battle_440111_Cut_000', f'SEQ_Battle_{sid+1}_Master']]})
        jobs.append({'asset': asset, 'plan': plan, 'audio': None, 'kind': 'skill_motion'})
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
            original = rows(rel); donor = next((k for k, v in original.items() if v['ID'] == 440111), None)
            if donor is None: raise ValueError('The game has no compatible battle timeline row.')
            occupied = {v['ID'] for v in original.values()}
            for off in (1, 2):
                if sid + off in occupied: continue
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                    'row': f'Studio_Motion_{sid}_{off}', 'cloneFrom': donor,
                    'set': {'ID': sid+off, 'LevelSequence': asset.replace('FFRS/Content/', '/Game/'), 'soundSequence': 'None', 'bChangeNearClipPlane': False}})
        rel = 'Battle/Sequencer/DT_BtlHitEffectData'; original = rows(rel)
        if not any(v['ID'] == sid for v in original.values()):
            donor = next((k for k, v in original.items() if v['ID'] == 449999), None)
            if donor is None: raise ValueError('The game has no compatible battle reaction row.')
            supportive = skill.get('defaultTargetRelation', '').split('::')[-1] == 'Friendlies'
            tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                'row': f'Studio_Motion_{sid}', 'cloneFrom': donor,
                'set': ffbe_resonance.reaction_settings(sid) if supportive else {'ID': sid}})
        repaired.append(sid)
    if repaired:
        print('  Added attack/casting timelines for selected skills: ' + ', '.join(map(str, repaired)))
        print('  These repairs play unit motions; missing original particle effects remain unverified.')
    return repaired
