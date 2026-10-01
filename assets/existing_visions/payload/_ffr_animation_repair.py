"""Recover FFBE motions, reuse compatible native sequences, and fill motion gaps.

Original skill mechanics and existing sequences are never replaced. The asset
dump provides unit motions, not the missing spell/ability particle effects.
"""
import csv
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
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


NORMAL_SKILLS = {'Ability', 'Magic', 'MagicSword', 'Fight'}
# These affect numbers in the skill table, not the sequence's choreography.
VISUAL_METADATA = {'ID', 'SortId', 'Name', 'Description', 'SkillIcon', 'hasUnit', 'Cost',
                   'magnification', 'breakDamageValue', 'accuracy'}
NORMAL_EVENTS = {'None', 'UnitPlayAnimByName', 'UnitMoveToTarget', 'UnitMoveToDefaultLocation',
                 'OtherReaction', 'EffectSpawnNiagaraAtTarget', 'EffectSpawnNiagaraAtRandom',
                 'SoundPlayHitSound', 'CameraShake', 'CameraSetDefault', 'CameraSetZoomInOut',
                 'PostSetDefaultColorGrading', 'PostSetColorGradingGlobalParameter'}
NORMAL_MOTIONS = {'idle', 'command', 'magic_idle', 'magic_attack', 'M_attack01', 'M_attack02',
                  'attack_A', 'attack_B', 'attack_C', 'attack_D', 'attack_E'}


def enum(value):
    return str(value or '').split('::')[-1]


class NativeAnimations:
    """Consider same-name variants only; audit actual packages before reusing them.

    Matching the complete mechanics (except numeric strength/cost) also checks
    targets, hit ratios, timing flags and effect bundles omitted by the UI catalog.
    An animation donor never supplies the recipient's skill mechanics.
    """
    def __init__(self, rows, root, extract, support):
        self.root = Path(root); self.extract = extract; self.support = support
        self.skills = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
        self.assets = {rel: rows(rel) for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo')}
        self.reactions = rows('Battle/Sequencer/DT_BtlHitEffectData')
        self.effects = {r['ID']: r for r in rows('Skill/DT_SkillEffectData').values()}
        self.names = {}
        # The prepared catalog takes priority. Bundled names are just a fallback;
        # all mechanics and sequence bindings always come from this game install.
        for file in ('build/devui/ffr_catalog.json', 'data/ffr_catalog.json'):
            path = self.root / file
            if path.is_file():
                self.names = {s['id']: s.get('name', '') for s in json.loads(path.read_bytes())['skills']}
                break
        locale = self.root / 'extracted/locres_en.json'
        strings = json.loads(locale.read_bytes()) if locale.is_file() else {}
        for sid, skill in self.skills.items():
            name = skill.get('Name')
            if isinstance(name, str) and name: self.names[sid] = name
            elif isinstance(name, dict):
                ns = name.get('table', '').split('/')[-1].split('.')[-1]
                translated = (strings.get(ns) or {}).get(name.get('key'))
                if translated: self.names[sid] = translated
        self.signatures = {sid: self.signature(s) for sid, s in self.skills.items()}
        self.audits = {}

    def signature(self, skill):
        data = {k: copy.deepcopy(v) for k, v in skill.items() if k not in VISUAL_METADATA}
        for bundle in data.get('effectBundleList', []):
            effect = self.effects.get(bundle.get('effectId'))
            if effect:
                bundle['effectId'] = {k: v for k, v in effect.items()
                                      if k not in {'ID', 'SortId', 'Name', 'Description'}}
        return json.dumps(data, sort_keys=True, ensure_ascii=False)

    def candidates(self, skill):
        name = self.names.get(skill['ID'], '').strip().casefold()
        if not name or enum(skill.get('skillAttrType')) not in NORMAL_SKILLS: return []
        signature = self.signature(skill)
        return sorted((sid for sid, donor in self.skills.items()
                       if enum(donor.get('hasUnit')) == 'All'
                       and self.names.get(sid, '').strip().casefold() == name
                       and self.signatures[sid] == signature
                       and any(r['ID'] in (sid, sid+1, sid+2) for r in self.assets['Asset/Skill/DT_SkillAsset'].values())),
                      key=lambda sid: (abs(skill['ID'] - sid), sid))

    def audit(self, asset, donor, hits):
        key = (asset.get('LevelSequence'), donor, hits)
        if key not in self.audits:
            try: self.audits[key] = self._audit(asset, donor, hits)
            except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError, subprocess.SubprocessError) as error:
                self.audits[key] = f'Native sequence could not be verified: {error}'
        return self.audits[key]

    def _audit(self, asset, donor, hits):
        master = asset.get('LevelSequence', '').split('.')[0]
        if not master.startswith('/Game/Sequencer/Battle/'): return 'Not an ordinary battle sequence.'
        relative = master.removeprefix('/Game/')
        folder = self.root / 'extracted/legacy/FFRS/Content' / str(Path(relative).parent)
        if not folder.resolve().is_relative_to((self.root / 'extracted/legacy').resolve()):
            return 'Invalid native sequence path.'
        source = folder / (Path(relative).name + '.uasset')
        if not source.is_file(): self.extract(str(Path(relative).parent).replace('\\', '/') + '/')
        if not source.is_file(): return 'Native sequence package is absent from this game.'
        source_id = re.fullmatch(r'SEQ_Battle_(\d+)_Master', Path(relative).name)
        if not source_id: return 'Unrecognized native sequence identity.'
        reactions = 0; motions = 0; reaction_ids = set()
        valid_reactions = {r['ID'] for r in self.reactions.values()}
        for path in sorted(folder.rglob('*.uasset')):
            tj, dump = self.support['dumps'](str(path))
            if not tj or dump is None: return 'Native sequence could not be decoded.'
            imports = [str(i.get('ObjectName', '')) for i in tj.get('Imports', [])]
            if any(i in {'MovieSceneMediaTrack', 'MovieSceneCinematicShotTrack', 'MovieSceneSpawnTrack'}
                   or i.startswith('VO_') or '/Chara/summon/' in i for i in imports):
                return 'Sequence contains an owner-specific actor, movie or voice.'
            if any(i.startswith('/Game/Sequencer/') and not i.startswith('/Game/' + str(Path(relative).parent).replace('\\', '/') + '/')
                   for i in imports): return 'Sequence references an unaudited external sequence.'
            functions = {k.split(':', 1)[-1]: value for k, value in dump.items()}
            for tick, event_type, name in self.support['keys'](str(path)):
                event = functions.get(name)
                if not isinstance(tick, (int, float)) or not isinstance(event, dict): return 'Unresolved battle event.'
                kind = enum(event_type)
                if kind not in NORMAL_EVENTS: return f'Special battle event: {kind}.'
                if kind == 'UnitPlayAnimByName':
                    if event.get('Unit_PlayAnimByName_AnimationName') not in NORMAL_MOTIONS:
                        return 'Sequence requires a specialized unit motion.'
                    motions += 1
                elif kind == 'OtherReaction':
                    reaction = event.get('Other_Reaction_Id')
                    if type(reaction) is not int or reaction not in valid_reactions or event.get('Otber_Reaction_ReactionNum') != -1:
                        return 'Sequence has specialized hit/reaction routing.'
                    reaction_ids.add(reaction)
                    reactions += 1
        if reactions != hits: return 'Sequence hit timing does not match the recipient.'
        if not motions: return 'Sequence has no verified unit motion.'
        if len(reaction_ids) != 1: return 'Sequence switches between specialized reaction types.'
        return {'sequenceId': int(source_id[1]), 'reactionId': reaction_ids.pop()}

    def reuse(self, sid, skill, tables, clones):
        target = enum(skill.get('TargetType'))
        if target not in {'Single', 'Group', 'Self'}: return None, 'Specialized targeting.'
        hits = int(skill.get('hitCount') or 1)
        if not 0 < hits <= 30: return None, 'Unsupported hit count.'
        required = 2 if target == 'Group' else 1
        candidates = self.candidates(skill); reason = 'No compatible same-name native animation.'
        for donor in candidates:
            primary = self.assets['Asset/Skill/DT_SkillAsset']
            offset = required if any(r['ID'] == donor + required for r in primary.values()) else 0
            bindings = {}
            for rel, original in self.assets.items():
                found = next(((k, r) for k, r in original.items() if r['ID'] == donor + offset), None)
                occupied = {r['ID'] for r in original.values()}
                occupied.update(r['set']['ID'] for r in tables.get(rel, {}).get('add', []) if 'ID' in r.get('set', {}))
                if not found or sid + offset in occupied: break
                # Both lookup tables must agree on the actual timeline.
                if bindings and found[1].get('LevelSequence') != next(iter(bindings.values()))[1].get('LevelSequence'): break
                bindings[rel] = found
            if len(bindings) != len(self.assets):
                reason = 'Missing or conflicting single/group sequence binding.'; continue
            verified = self.audit(bindings['Asset/Skill/DT_SkillAsset'][1], donor, hits)
            if not isinstance(verified, dict): reason = verified; continue
            # Group/enemy spell rows can share a sequence whose embedded IDs
            # belong to the single-target version rather than the donor row.
            edits = {kind: [{'match': {'EventType': 'OtherReaction', 'Other_Reaction_Id': verified['reactionId']},
                             'set': {'Other_Reaction_Id': sid}}] for kind in ('master', 'cut', 'effect', 'sound')}
            for rel, (key, asset) in bindings.items():
                copied = self.support['clone'](asset, verified['sequenceId'], sid, sid + offset, (), clones,
                                               self.support['objects'], (), edits, self.support['bytecode'])
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                    'row': f'Studio_NativeAnimation_{sid}_{offset}', 'cloneFrom': key, 'set': {'ID': sid + offset, **copied}})
            rel = 'Battle/Sequencer/DT_BtlHitEffectData'
            occupied = {r['ID'] for r in self.reactions.values()}
            occupied.update(r['set']['ID'] for r in tables.get(rel, {}).get('add', []) if 'ID' in r.get('set', {}))
            reaction = next((k for k, r in self.reactions.items() if r['ID'] == verified['reactionId']), None)
            if sid not in occupied and reaction:
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                    'row': f'Studio_NativeAnimation_{sid}', 'cloneFrom': reaction, 'set': {'ID': sid}})
            return donor, None
        return None, reason


def motion_seconds(unit, root, magic):
    ff = unit.get('ffbe') or {}; motion = 'magicatk' if magic else 'atk'
    for directory, form in ((ff.get('dir'), ff.get('id')), (ff.get('baseDir'), ff.get('baseForm'))):
        if not directory or not form: continue
        for name in (motion, ALIASES.get(motion, motion), *(() if magic else ('atk1', 'attack'))):
            p = Path(root) / directory / f'unit_{name}_cgs_{form}.csv'
            if p.is_file():
                return max(0.1, sum(max(1, int(s[3])) for s in csv_rows(p.read_bytes()) if len(s) >= 4) / 60)
    return 1.0


def prepare_sequences(tables, clones, jobs, units, root, rows, extract, native_support=None):
    """Add selected missing skill timelines; leave existing game rows untouched."""
    skill_rows = rows('Skill/DT_SkillData'); by_id = {r['ID']: r for r in skill_rows.values()}
    selected = {}
    for unit in units:
        for tier in [*unit.get('awakening', []), *unit.get('synchro', [])]:
            for grant in tier:
                if grant[0] == 'ActiveSkill': selected.setdefault(int(grant[1]), []).append(unit)
    native = None
    if native_support:
        try: native = NativeAnimations(rows, root, extract, native_support)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f'  Native animation matching unavailable: {error}. Keeping attack/casting repair.')
    repaired = []; reused = []; coverage = []
    for sid, owners in sorted(selected.items()):
        if sequence_present(sid, rows, tables):
            coverage.append({'id': sid, 'status': 'existing_sequence'}); continue
        recipes = [(u.get('skills') or {}).get(str(sid), (u.get('skills') or {}).get(sid)) for u in owners]
        recipe = next((r for r in recipes if r), None)
        base = by_id.get(recipe['from'] if recipe else sid)
        if not base:
            coverage.append({'id': sid, 'status': 'unresolved', 'reason': 'Skill definition unavailable.'}); continue
        skill = {**base, **((recipe or {}).get('set') or {})}
        donor, reason = native.reuse(sid, skill, tables, clones) if native else (None, 'Native sequence audit unavailable.')
        if donor is not None:
            repaired.append(sid); reused.append((sid, donor))
            coverage.append({'id': sid, 'status': 'native_reuse', 'donor': donor}); continue
        if enum(skill.get('skillAttrType')) not in NORMAL_SKILLS:
            coverage.append({'id': sid, 'status': 'unresolved', 'reason': 'Specialized skill type.'}); continue
        magic = skill.get('skillAttrType', '').split('::')[-1] in ('Magic', 'MagicSword') or skill.get('DamageType', '').split('::')[-1] != 'Physic'
        hits = int(skill.get('hitCount') or 1)
        if not 0 < hits <= 30:
            coverage.append({'id': sid, 'status': 'unresolved', 'reason': 'Unsupported hit count.'}); continue
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
        coverage.append({'id': sid, 'status': 'motion_fallback', 'nativeReason': reason})
    if reused:
        print('  Reused audited native animations (skill <- animation donor): ' + ', '.join(f'{sid} <- {donor}' for sid, donor in reused))
    fallback = [entry['id'] for entry in coverage if entry['status'] == 'motion_fallback']
    if fallback:
        print('  Added attack/casting timelines for selected skills: ' + ', '.join(map(str, fallback)))
        print('  These repairs play unit motions; missing original particle effects remain unverified.')
    # Fresh per-build coverage; includes ordinary learned skills and separate
    # finishing/Resonance IDs without altering any saved roster specification.
    for unit in units:
        if not unit.get('lb_custom') and unit.get('lb') and int(unit['lb']) not in selected:
            sid = int(unit['lb'])
            if not any(e['id'] == sid for e in coverage):
                coverage.append({'id': sid, 'status': 'existing_sequence' if sequence_present(sid, rows, tables) else 'unresolved',
                                 'role': 'resonance'})
    report = Path(root) / 'build/animation-repair-report.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'schema': 1, 'inGameValidated': False, 'skills': coverage}, indent=2) + '\n', encoding='utf-8')
    return repaired
