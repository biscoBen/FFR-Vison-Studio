"""Recover FFBE motions and reuse native visual effects without donor mechanics.

Original skill mechanics and existing sequences are never replaced. Native
particles retain their import references in separately authored motion timelines.
"""
import csv
import copy
import hashlib
import io
import json
import math
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
RELEASE_MOTIONS = NORMAL_MOTIONS - {'idle', 'command', 'magic_idle'}

# Explicit visual-only prototypes. A source label is never an automatic donor.
# These IDs and donor bindings are from the supported game's catalog. Effects,
# damage, ratios and targeting always remain those of the receiving skill.
ANIMATION_PROFILES = {
    400310: {'name': 'Bladeblitz', 'donor': 501310, 'donorName': 'Grand Slash',
             'prepare': 'command', 'release': 'attack_A',
             'expected': ('Ability', 'Physic', 'None', 'Group', 'Enemies', 1)},
    420130: {'name': 'Aero Blade', 'donor': 220170, 'donorName': 'Aero',
             'prepare': 'magic_idle', 'release': 'attack_A',
             'expected': ('MagicSword', 'Physic', 'Wind', 'Single', 'Enemies', 1)},
    414410: {'name': 'Aquatic Synergy', 'donor': 220150, 'donorName': 'Waterga',
             'prepare': 'command', 'release': 'attack_A',
             'expected': ('Ability', 'Physic', 'Water', 'Single', 'Enemies', 3)},
    210150: {'name': 'Arise', 'donor': 210140, 'donorName': 'Raise',
             'prepare': 'magic_idle', 'release': 'magic_attack',
             'expected': ('Magic', 'Magic', 'None', 'Single', 'Friendlies', 1)},
}


def enum(value):
    return str(value or '').split('::')[-1]


ELEMENT_DONORS = {
    'Fire': (220010, 220020, 220030), 'Ice': (220050, 220060, 220070),
    'Thunder': (220090, 220100, 220110), 'Water': (220130, 220140, 220150),
    'Wind': (220170, 220180, 220190), 'Earth': (220210, 220220, 220230),
    # Banishga/Dark's ordinary timelines are absent. Reuse portable target
    # effects from the strongest available light spell / Dystopia instead.
    'Light': (210250, 210260, 210260), 'Dark': (408050, 408050, 408050),
}
PHYSICAL_DONORS = {'Thunder': (420070, 420080, 420090), 'Earth': (420160, 420170, 420180)}
# These fixed-damage skills have no dedicated sequence in the game catalog.
# Borrow ordinary monster Needle's shared Stab/Needle particles, not its body,
# physical-damage formula or hit count.
MONSTER_NEEDLES = {500270: ('1,000 Needles', 1000), 505110: ('10,000 Needles', 10000)}
EFFECT_EVENTS = {'EffectSpawnNiagaraAtTarget', 'EffectSpawnNiagaraAtRandom', 'EffectMoveNiagaraAtTargetToNiagaraID',
                 'EffectMoveNiagaraAddVectorToNiagaraID', 'EffectDiactivateNiagaraToNiagaraID',
                 'EffectDestroyNiagaraToNiagaraID', 'EffectSetUserParameterToNiagaraID'}
REACTION_VISUAL_FIELDS = {'NormalEffectID', 'CriticalEffectID', 'WeaknessEffectID', 'MissEffectID',
                          'AdditionalEffectID', 'DeathEffectID', 'IsAdditionalEffect', 'PlayShakeID'}


def reaction_visuals(row):
    return {k: copy.deepcopy(v) for k, v in row.items() if k in REACTION_VISUAL_FIELDS}


def expected_reaction_edits(root, units, rows):
    """Reconstruct audited cosmetic edits for the existing exact-field verifier.

    The report identifies the audited source row; expected values come from
    original extracted game data, never the built row or an unrestricted patch.
    """
    root = Path(root); report = root / 'build/animation-repair-report.json'
    if not report.is_file(): return {}
    catalog = next((root / name for name in ('build/devui/ffr_catalog.json', 'data/ffr_catalog.json')
                    if (root / name).is_file()), None)
    if catalog is None: return {}
    policy = effect_policy(json.loads(catalog.read_bytes()))['skills']
    selected = {int(g[1]) for u in units for tier in [*u.get('awakening', []), *u.get('synchro', [])]
                for g in tier if g[0] == 'ActiveSkill'}
    custom = {int(sid) for u in units for sid, recipe in (u.get('skills') or {}).items() if recipe}
    rel = 'Battle/Sequencer/DT_BtlHitEffectData'; originals = rows(rel); expected = {}
    record = json.loads(report.read_bytes())
    if record.get('schema') != 1: return {}
    for entry in record.get('skills', []):
        sid = entry.get('id'); mapping = policy.get(str(sid))
        if (entry.get('status') != 'effect_reuse' or sid not in selected or sid in custom or not mapping
                or any(entry.get(k) != mapping[k] for k in ('donor', 'rule', 'tier'))
                or sequence_present(sid, rows, {})):
            continue
        source_key = entry.get('reactionRow'); source = originals.get(source_key)
        if not source: continue
        # Prefer the donor's own row just as the author does. Shared timelines
        # may have an audited alternate reaction when that direct row is absent.
        direct = next((k for k, r in originals.items() if r['ID'] == mapping['donor']), None)
        if direct is not None and source_key != direct: continue
        target = next((k for k, r in originals.items() if r['ID'] == sid), None)
        if target is not None: expected[(rel, target)] = reaction_visuals(source)
    return expected


def particle_import(raw, imports, known_particles=()):
    """Resolve seqdump's object label to the actual cooked particle import."""
    if type(raw) is int and raw < 0:
        matches = [-raw - 1] if -raw <= len(imports) else []
    else:
        name = str(raw).removeprefix('import:')
        matches = [i for i, item in enumerate(imports) if item.get('ObjectName') == name]
    if len(matches) != 1: raise ValueError(f'Unresolved or ambiguous particle import: {raw}.')
    ref = matches[0]; obj = imports[ref]
    if obj.get('ClassName') != 'NiagaraSystem': raise ValueError('The effect is not a portable Niagara system.')
    outer = obj.get('OuterIndex', 0)
    package = imports[-outer - 1].get('ObjectName', '') if type(outer) is int and -len(imports) <= outer < 0 else ''
    if not package.startswith('/Game/Effect/') or (known_particles and package not in known_particles):
        raise ValueError('The donor particle is outside the game effect catalog.')
    return ref, {'path': package + '.' + obj['ObjectName'], 'class': 'NiagaraSystem'}


def particle_constants(value, imports, known_particles, references):
    """Translate every particle object constant, including secondary spawns."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key in ('niagaraAsset', 'friendNiagaraAsset', 'enemyNiagaraAsset') or (isinstance(child, str) and child.startswith('import:')):
                if child is None or child == 'None' or child == 0:
                    result[key] = None
                else:
                    ref, result[key] = particle_import(child, imports, known_particles)
                    references.append({'imports': imports, 'index': ref})
            else: result[key] = particle_constants(child, imports, known_particles, references)
        return result
    if isinstance(value, list): return [particle_constants(child, imports, known_particles, references) for child in value]
    return copy.deepcopy(value)


def verify_particle_constants(expected, actual, imports):
    if isinstance(expected, dict):
        if expected.get('class') == 'NiagaraSystem' and 'path' in expected:
            _, retained = particle_import(actual, imports)
            if retained != expected: raise ValueError(f'The written particle reference differs from {expected["path"]}.')
        else:
            for key, child in expected.items():
                verify_particle_constants(child, actual.get(key) if isinstance(actual, dict) else None, imports)
    elif isinstance(expected, list):
        for i, child in enumerate(expected):
            verify_particle_constants(child, actual[i] if isinstance(actual, list) and i < len(actual) else None, imports)


def effect_tier(skill):
    name = str(skill.get('name') or '').casefold()
    if re.search(r'\biii\b', name) or name.startswith(('firaga', 'blizzaga', 'thundaga', 'waterga', 'aeroga', 'stonega', 'banishga', 'darkga')):
        return 3
    if re.search(r'\bii\b', name) or name.startswith(('fira', 'blizzara', 'thundara', 'watera', 'aerora', 'stonera', 'banishra', 'darkra')):
        return 2
    power = float(skill.get('mag') or 0)
    return 1 if power <= 25 else 2 if power <= 45 else 3


def effect_policy(catalog):
    """Visual mapping only: never change duplicate/hiding verification."""
    skills = {s['id']: s for s in catalog.get('skills', [])}
    def usable(s):
        return bool(s.get('seq')) and s.get('attr') in NORMAL_SKILLS
    native = [s for s in skills.values() if usable(s) and s.get('hasUnit') == 'All' and s['id'] < 460000]
    result = {}
    for sid, skill in skills.items():
        if skill.get('seq') or skill.get('attr') not in NORMAL_SKILLS or not 0 < int(skill.get('hits') or 0) <= 30:
            continue
        name = str(skill.get('name') or '').strip().casefold()
        same = [s for s in native if name and str(s.get('name') or '').strip().casefold() == name]
        donor = None; rule = None; tier = effect_tier(skill)
        if sid in MONSTER_NEEDLES and skill.get('name') == MONSTER_NEEDLES[sid][0] and skill.get('calcType') == 'Fixed':
            donor = skills.get(500260); rule = 'monster_needle'
        elif same:
            donor = min(same, key=lambda s: (s.get('target') != skill.get('target'),
                        s.get('dmgType') != skill.get('dmgType'), s['id']))
            rule = 'same_name'
        elif sid in ANIMATION_PROFILES and skill.get('name') == ANIMATION_PROFILES[sid]['name']:
            donor = skills.get(ANIMATION_PROFILES[sid]['donor']); rule = 'explicit_profile'
        elif skill.get('element') in ELEMENT_DONORS and skill.get('dmgType') in ('Physic', 'Magic') and float(skill.get('mag') or 0) > 0:
            family = (PHYSICAL_DONORS.get(skill['element']) if skill['dmgType'] == 'Physic' else None) or ELEMENT_DONORS[skill['element']]
            donor = skills.get(family[tier - 1]); rule = 'element_tier'
        if donor and usable(donor):
            result[str(sid)] = {'donor': donor['id'], 'donorName': donor['name'], 'rule': rule, 'tier': tier}
    trials = {str(sid): {'source': source} for sid, source in
              ((400260, 'FFR'), (400300, 'FFBE'), (500270, 'FFR mob'), (505110, 'FFR mob'))
              if sid in skills and not skills[sid].get('seq')}
    return {'schema': 1, 'skills': result, 'trials': trials}


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
        self.names = {}; self.catalog = {}
        # The prepared catalog takes priority. Bundled names are just a fallback;
        # all mechanics and sequence bindings always come from this game install.
        for file in ('build/devui/ffr_catalog.json', 'data/ffr_catalog.json'):
            path = self.root / file
            if path.is_file():
                self.catalog = json.loads(path.read_bytes())
                self.names = {s['id']: s.get('name', '') for s in self.catalog['skills']}
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
        self.visual_policy = effect_policy(self.catalog)['skills']

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

    def target_effects(self, sid):
        """Read just the donor's particle events and their actual import trees.

        Caster motions, camera/voice tracks and OtherReaction events never enter
        the receiving timeline. Its own schedule supplies every damaging hit.
        """
        mapping = self.visual_policy[str(sid)]; donor = mapping['donor']
        primary = self.assets['Asset/Skill/DT_SkillAsset']
        target = enum(self.skills[sid].get('TargetType'))
        preferred = 2 if target in ('Group', 'All') else 1
        binding = next((r for off in (preferred, 0, 1, 2) for r in primary.values() if r['ID'] == donor + off), None)
        if not binding: raise ValueError(f'{mapping["donorName"]} has no native sequence binding.')
        master = binding.get('LevelSequence', '').split('.')[0]
        if not master.startswith('/Game/Sequencer/Battle/'): raise ValueError('Invalid donor sequence path.')
        relative = Path(master.removeprefix('/Game/'))
        folder = self.root / 'extracted/legacy/FFRS/Content' / relative.parent
        if not folder.resolve().is_relative_to((self.root / 'extracted/legacy').resolve()):
            raise ValueError('Donor sequence escapes the extracted game folder.')
        if not (folder / (relative.name + '.uasset')).is_file():
            self.extract(str(relative.parent).replace('\\', '/') + '/')
        if not (folder / (relative.name + '.uasset')).is_file(): raise ValueError('The donor sequence was not extracted.')
        packets = []; imports = []; reactions = set()
        known_particles = set(self.catalog.get('niagara', []))
        for path in sorted(folder.rglob('*.uasset')):
            tj, dump = self.support['dumps'](str(path))
            if not tj or dump is None: raise ValueError(f'Could not decode {path.name}.')
            functions = {k.split(':', 1)[-1]: value for k, value in dump.items()}
            for tick, kind, name in self.support['keys'](str(path)):
                event = functions.get(name, {}); kind = enum(kind)
                if kind == 'OtherReaction': reactions.add(event.get('Other_Reaction_Id'))
                if kind not in EFFECT_EVENTS: continue
                if kind == 'EffectSpawnNiagaraAtRandom': kind = 'EffectSpawnNiagaraAtTarget'
                if isinstance(tick, bool) or not isinstance(tick, (int, float)) or not math.isfinite(tick) or tick < 0:
                    raise ValueError('Invalid donor effect time.')
                st = particle_constants({k: v for k, v in event.items() if k.startswith('Effect_')},
                                        tj.get('Imports', []), known_particles, imports)
                st['EventType'] = kind
                if kind == 'EffectSpawnNiagaraAtTarget':
                    data = st.get('Effect_NiagaraData')
                    if not isinstance(data, dict): raise ValueError('Missing native particle parameters.')
                    if not isinstance(data.get('niagaraAsset'), dict): raise ValueError('Missing native particle import.')
                if any('/Chara/' in str(v) or 'VO_' in str(v) for v in st.values()):
                    raise ValueError('Effect parameters reference a character or voice.')
                # Target the receiving skill's selected combatants. A donor's
                # scene-wide flag must not expose unrelated allies/enemies.
                for key in st:
                    if 'AllSide' in key: st[key] = False
                packets.append({'time': tick, 'set': st})
        if not any(p['set']['EventType'] == 'EffectSpawnNiagaraAtTarget' for p in packets):
            raise ValueError(f'{mapping["donorName"]} has no reusable target particle events.')
        # The original reaction row is cosmetic; it can differ from the catalog
        # ID when single/group spell variants share a timeline.
        reaction = next((k for k, r in self.reactions.items() if r['ID'] == donor), None)
        reaction = reaction or next((k for k, r in self.reactions.items() if r['ID'] in reactions), None)
        return {**mapping, 'events': packets, 'imports': imports, 'reactionRow': reaction}

    def bind_reaction_visuals(self, sid, bundle, tables):
        key = bundle.get('reactionRow')
        if key is None: return
        rel = 'Battle/Sequencer/DT_BtlHitEffectData'
        visual = reaction_visuals(self.reactions[key])
        existing = next((k for k, r in self.reactions.items() if r['ID'] == sid), None)
        spec = tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
        added = next((r for r in spec['add'] if r.get('set', {}).get('ID') == sid), None)
        if added: added['set'].update(visual)
        elif existing: spec['set'].append({'row': existing, 'set': visual})
        else: spec['add'].append({'row': f'Studio_Effects_{sid}', 'cloneFrom': key, 'set': {'ID': sid, **visual}})

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

    def profile(self, sid, skill, owners, tables, clones):
        """Borrow an audited visual timeline, never its mechanics or hit count.

        Unlike automatic same-name matching, only these four explicit mappings
        may use a mechanically different donor. Each must have matching targets
        and hit counts, portable events, and complete prepare/release/idle phases.
        """
        profile = ANIMATION_PROFILES[sid]
        actual = tuple(enum(skill.get(k)) for k in ('skillAttrType', 'DamageType', 'element',
                       'TargetType', 'defaultTargetRelation')) + (int(skill.get('hitCount') or 1),)
        if self.names.get(sid) != profile['name'] or actual != profile['expected']:
            return None, 'The skill no longer matches its animation profile.'
        donor = self.skills.get(profile['donor'])
        if (not donor or self.names.get(donor['ID']) != profile['donorName']
                or enum(donor.get('hasUnit')) != 'All'
                or enum(donor.get('TargetType')) != actual[3]
                or enum(donor.get('defaultTargetRelation')) != actual[4]
                or int(donor.get('hitCount') or 1) != actual[5]):
            return None, 'The visual donor has incompatible targeting or hit count.'
        offset = 2 if actual[3] == 'Group' else 1
        assets = self.assets['Asset/Skill/DT_SkillAsset']
        binding = next(((k, r) for k, r in assets.items() if r['ID'] == donor['ID'] + offset), None)
        binding = binding or next(((k, r) for k, r in assets.items() if r['ID'] == donor['ID']), None)
        if not binding: return None, 'The visual donor has no target-compatible binding.'
        secondary = next(((k, r) for k, r in self.assets['Asset/Skill/CDT_SkillAsset_Demo'].items()
                          if r['ID'] == binding[1]['ID']), None)
        if not secondary or secondary[1].get('LevelSequence') != binding[1].get('LevelSequence'):
            return None, 'The donor lookup tables disagree.'
        # Reserve private sequence identities even if a donor happens to use
        # the recipient's original sequence path (Grand Slash/Bladeblitz).
        sequence = 800000000 + sid + 1
        if any(re.search(rf'/SEQ_Battle_{sequence}_Master(?:\.|$)', r.get('LevelSequence', ''))
               for original in self.assets.values() for r in original.values()):
            return None, 'The private animation sequence identity is already in use.'
        verified = self.audit(binding[1], donor['ID'], actual[5])
        if not isinstance(verified, dict): return None, verified
        try:
            motion_edits, rates = self.profile_motions(binding[1], owners, profile)
        except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError, subprocess.SubprocessError) as error:
            return None, f'The visual phases could not be verified: {error}'
        edits = {kind: [{'match': {'EventType': 'OtherReaction', 'Other_Reaction_Id': verified['reactionId']},
                         'set': {'Other_Reaction_Id': sid}}, *copy.deepcopy(motion_edits)]
                 for kind in ('master', 'cut', 'effect', 'sound')}
        copied = self.support['clone'](binding[1], verified['sequenceId'], sid, sequence, (), clones,
                                       self.support['objects'], (), edits, self.support['bytecode'])
        for rel, key in (('Asset/Skill/DT_SkillAsset', binding[0]), ('Asset/Skill/CDT_SkillAsset_Demo', secondary[0])):
            occupied = {r['ID'] for r in self.assets[rel].values()}
            occupied.update(r['set']['ID'] for r in tables.get(rel, {}).get('add', []) if 'ID' in r.get('set', {}))
            for off in (1, 2):
                if sid + off in occupied: continue
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                    'row': f'Studio_Profile_{sid}_{off}', 'cloneFrom': key, 'set': {'ID': sid + off, **copied}})
        rel = 'Battle/Sequencer/DT_BtlHitEffectData'
        occupied = {r['ID'] for r in self.reactions.values()}
        occupied.update(r['set']['ID'] for r in tables.get(rel, {}).get('add', []) if 'ID' in r.get('set', {}))
        if sid not in occupied:
            reaction = next(k for k, r in self.reactions.items() if r['ID'] == verified['reactionId'])
            tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                'row': f'Studio_Profile_{sid}', 'cloneFrom': reaction, 'set': {'ID': sid}})
        return {'profile': profile['name'], 'donor': donor['ID'], 'prepareMotion': profile['prepare'],
                'releaseMotion': profile['release'], 'playRates': rates}, None

    def profile_motions(self, asset, owners, profile):
        folder = self.root / 'extracted/legacy/FFRS/Content' / str(Path(asset['LevelSequence'].split('.')[0].removeprefix('/Game/')).parent)
        motions = []; moves = []; returns = []
        for path in sorted(folder.rglob('*.uasset')):
            tj, dump = self.support['dumps'](str(path))
            if any('/Chara/' in str(i.get('ObjectName', '')) and '/Chara/effect/' not in str(i.get('ObjectName', ''))
                   for i in tj.get('Imports', [])):
                raise ValueError('The timeline imports an owner-specific character.')
            events = {k.split(':', 1)[-1]: v for k, v in dump.items()}
            for tick, kind, name in self.support['keys'](str(path)):
                event = events[name]
                if isinstance(tick, bool) or not math.isfinite(tick) or tick < 0:
                    raise ValueError('The timeline has an invalid event time.')
                if enum(kind) == 'SoundPlayHitSound' and re.search(r'\bVO[_ ]', json.dumps(event)):
                    raise ValueError('The timeline uses an owner-specific voice.')
                if enum(kind) == 'UnitPlayAnimByName': motions.append((tick, event))
                elif enum(kind) == 'UnitMoveToTarget': moves.append(tick)
                elif enum(kind) == 'UnitMoveToDefaultLocation': returns.append(tick)
        motions.sort(key=lambda item: item[0])
        if moves and (not returns or max(returns) <= max(moves)):
            raise ValueError('The timeline does not return the caster to its position.')
        names = {e.get('Unit_PlayAnimByName_AnimationName') for _, e in motions}
        if not names.intersection({'command', 'magic_idle'}) or not names.intersection(RELEASE_MOTIONS) or 'idle' not in names:
            raise ValueError('The timeline lacks separate preparation, release or recovery.')
        seconds = max(motion_seconds(u, self.root, profile['release'] == 'magic_attack') for u in owners)
        rates = {}
        for tick, event in motions:
            name = event.get('Unit_PlayAnimByName_AnimationName')
            if name not in RELEASE_MOTIONS: continue
            end = next((t for t, _ in motions if t > tick), None)
            if end is None: raise ValueError('The release has no recovery phase.')
            # Fit the longest participating vision into the donor's motion
            # window. Hit keys/effects remain in place; no damage events added.
            rates[name] = max(rates.get(name, 1.0), 1.0, seconds * 24000 / (end - tick))
        last_release = max(t for t, e in motions if e.get('Unit_PlayAnimByName_AnimationName') in RELEASE_MOTIONS)
        if not any(t > last_release and e.get('Unit_PlayAnimByName_AnimationName') == 'idle' for t, e in motions):
            raise ValueError('The caster never returns to idle after release.')
        edits = [{'match': {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': name},
                  'set': {'Unit_PlayAnimByName_AnimationName': profile['prepare']}}
                 for name in sorted(names.intersection({'command', 'magic_idle'}))]
        edits += [{'match': {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': name},
                   'set': {'Unit_PlayAnimByName_AnimationName': profile['release'], 'Unit_PlayAnimByName_InStartFrame': 0,
                           'Unit_PlayAnimByName_InPlayRate': rate, 'Unit_PlayAnimByName_InLoopCount': 1}}
                  for name, rate in sorted(rates.items())]
        return edits, rates


def motion_seconds(unit, root, magic):
    ff = unit.get('ffbe') or {}; motion = 'magicatk' if magic else 'atk'
    for directory, form in ((ff.get('dir'), ff.get('id')), (ff.get('baseDir'), ff.get('baseForm'))):
        if not directory or not form: continue
        for name in (motion, ALIASES.get(motion, motion), *(() if magic else ('atk1', 'attack'))):
            p = Path(root) / directory / f'unit_{name}_cgs_{form}.csv'
            if p.is_file():
                return max(0.1, sum(max(1, int(s[3])) for s in csv_rows(p.read_bytes()) if len(s) >= 4) / 60)
    return 1.0


def prepare_barrage_trial(units, root, rows):
    """Prepare only selected Barrage owners; reuse their own cached FFBE inputs.

    FFBE Barrage repeats normal attacks. Native attack impact frames come from
    the pinned FFBE data; no FFBE damage values or extra hits enter FFR.
    """
    root = Path(root)
    owners = [u for u in units if any(g[0] == 'ActiveSkill' and int(g[1]) == 400300
              for tier in [*u.get('awakening', []), *u.get('synchro', [])] for g in tier)]
    config = {'schema': 1, 'owners': {}}
    if owners and not sequence_present(400300, rows, {}):
        skill = next((r for r in rows('Skill/DT_SkillData').values() if r['ID'] == 400300), {})
        signature = tuple(enum(skill.get(k)) for k in ('skillAttrType', 'DamageType', 'TargetType', 'defaultTargetRelation'))
        if signature != ('Ability', 'Physic', 'Random', 'Enemies') or skill.get('hitCount') != 4:
            raise ValueError('The FFBE Barrage trial requires the original four-hit FFR Barrage definition.')
        index = json.loads(Path(__file__).with_name('ffbe_barrage_index.json').read_bytes())
        if (index.get('schema') != 1 or index.get('repository') != 'aEnigmatic/ffbe'
                or index.get('commit') != '95727376e82d27acc1290b6dc8ad27ce3c89ea71'
                or index.get('skill') != {'id': 200310, 'name': 'Barrage', 'repeats': 4, 'moveType': 1, 'motionType': 1}):
            raise ValueError('Invalid pinned FFBE Barrage source.')
        for unit in owners:
            ff = unit.get('ffbe') or {}; chosen = None
            for directory, form in ((ff.get('dir'), ff.get('id')), (ff.get('baseDir'), ff.get('baseForm'))):
                if not directory or not form: continue
                folder = (root / directory).resolve()
                if not folder.is_relative_to(root.resolve()): raise ValueError('Barrage sprite path escapes the engine.')
                for motion in ('atk', 'atk1', 'attack', 'atk2', 'atk3'):
                    path = folder / f'unit_{motion}_cgs_{form}.csv'
                    if path.is_file():
                        steps = csv_rows(path.read_bytes())
                        if steps and all(len(s) >= 4 and int(s[3]) >= 0 for s in steps):
                            chosen = (str(form), sum(max(1, int(s[3])) for s in steps)); break
                if chosen: break
            if not chosen:
                raise ValueError(f'Barrage FFBE test needs FFBE attack sprites for {unit.get("en", unit.get("id"))}. Choose an FFBE-backed vision.')
            form, frames = chosen; impact = (index['forms'].get(form) or {}).get('impactFrame')
            if type(impact) is not int or not 0 < impact < frames:
                raise ValueError(f'Barrage FFBE attack timing is unavailable or incompatible for form {form}; cached sprites were kept.')
            config['owners'][str(unit['id'])] = {'form': form, 'frames': frames, 'impactFrame': impact}
        beat = max(p['impactFrame'] for p in config['owners'].values())
        config.update(cycleFrames=beat + max(p['frames'] - p['impactFrame'] for p in config['owners'].values()),
                      impactFrame=beat,
                      source={'repository': index['repository'], 'commit': index['commit'], 'skillId': 200310})
    path = root / 'build/barrage-trial.json'; path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.barrage-trial-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f: json.dump(config, f)
        os.replace(temporary, path)
    finally: Path(temporary).unlink(missing_ok=True)
    return config


def add_barrage_animation(spec, config, vision):
    """Repeat imported attack poses, fitting their impacts to shared FFR beats.

    Each recipient keeps its own cells and complete motion. Different FFBE
    attack lengths must not leave a shared skill's hits behind the body motion.
    """
    profile = config.get('owners', {}).get(str(vision))
    if not profile: return
    attack = next((a for a in spec['animations'] if a['name'] == 'attack_A'), None)
    if not attack or attack.get('fps') != 60 or attack.get('frameCount') != profile['frames']:
        raise ValueError('Barrage FFBE sprite conversion did not retain the expected attack motion.')
    length = profile['frames']; impact = profile['impactFrame']
    cycle = config['cycleFrames']; beat = config['impactFrame']
    animation = copy.deepcopy(attack); animation.update(name='FFBE_Barrage', frameCount=4 * cycle)
    for tracks in animation['parts'].values():
        for field, keys in tracks.items():
            repeated = []
            for repeat in range(4):
                for key in keys:
                    tick = key[0]
                    if type(tick) is not int or not 0 <= tick < length:
                        raise ValueError('Invalid imported Barrage attack keyframe.')
                    fitted = (round(tick * beat / impact) if tick <= impact else
                              beat + round((tick - impact) * (cycle - beat) / (length - impact)))
                    entry = [repeat * cycle + min(cycle - 1, fitted), *copy.deepcopy(key[1:])]
                    if repeated and entry[0] == repeated[-1][0]: repeated[-1] = entry
                    else: repeated.append(entry)
            tracks[field] = repeated
    spec['animations'] = [a for a in spec['animations'] if a['name'] != 'FFBE_Barrage'] + [animation]


def barrage_trial_plan(root, owners, skill):
    import ffbe_resonance
    path = Path(root) / 'build/barrage-trial.json'
    if not path.is_file(): raise ValueError('Prepare the FFBE Barrage trial before generating sprites.')
    config = json.loads(path.read_bytes())
    if config.get('schema') != 1 or any(str(u['id']) not in config.get('owners', {}) for u in owners):
        raise ValueError('The FFBE Barrage trial does not match the selected visions.')
    frames = config['cycleFrames']; beat = config['impactFrame']
    plan = ffbe_resonance.schedule(4 * frames / 60, 4, skill['ID'],
            source={'hitFrames': [i * frames + beat for i in range(4)]},
            movement={'enabled': True, 'right_shift': 0.0, 'target_offset': [0, 0, 0]})
    for event in plan['events']:
        st = event['set']
        if st.get('Unit_PlayAnimByName_AnimationName') == 'LB1': st['Unit_PlayAnimByName_AnimationName'] = 'FFBE_Barrage'
        elif st.get('Unit_PlayAnimByName_AnimationName') == 'LB1_before': st['Unit_PlayAnimByName_AnimationName'] = 'command'
    return plan


def steal_trial_plan(skill):
    """Make theft visible using the recipient, with one original resolution."""
    signature = tuple(enum(skill.get(k)) for k in ('skillAttrType', 'DamageType', 'TargetType', 'defaultTargetRelation'))
    if (signature != ('Ability', 'None', 'Single', 'Enemies') or skill.get('hitCount') != 1
            or not any(b.get('effectId') == 1030 for b in skill.get('effectBundleList', []))):
        raise ValueError('The FFR Steal trial requires the original item-stealing definition.')
    import ffbe_resonance
    plan = ffbe_resonance.schedule(1.0, 1, skill['ID'], source={'hitFrames': [24]},
            movement={'enabled': True, 'right_shift': 0.0, 'target_offset': [0, 0, 0]})
    # A ready/reach pose avoids turning theft into the recipient's sword attack
    # or adding a damaging hit. Movement and return are explicit timeline events.
    for event in plan['events']:
        st = event['set']
        if st.get('Unit_PlayAnimByName_AnimationName') in ('LB1', 'LB1_before'):
            st['Unit_PlayAnimByName_AnimationName'] = 'command'
    return plan


def add_target_effects(plan, bundle):
    """Fit cosmetic keys to our existing hit/recovery window; add no hits."""
    hits = [e['time'] for e in plan['events'] if e['set']['EventType'] == 'OtherReaction']
    idle = next(e['time'] for e in plan['events'] if e['set'].get('Unit_PlayAnimByName_AnimationName') == 'idle')
    packets = bundle['events']; start = min(p['time'] for p in packets); end = max(p['time'] for p in packets)
    first = hits[0] - 1
    for packet in packets:
        tick = first if end == start else first + round((packet['time'] - start) * (idle - first - 1) / (end - start))
        plan['events'].append({'time': tick, 'set': copy.deepcopy(packet['set'])})
    plan['events'].sort(key=lambda e: e['time'])


def effect_imports(asset, references):
    """Copy only referenced Niagara imports and ancestors into a cooked shell."""
    target = asset['Imports']; names = asset.get('NameMap', [])
    for reference in references:
        source = reference['imports']; visited = set(); mapped = {}
        def include(index):
            if index in mapped: return mapped[index]
            if index in visited or not 0 <= index < len(source): raise ValueError('Invalid particle import ancestry.')
            visited.add(index); item = copy.deepcopy(source[index]); outer = item.get('OuterIndex', 0)
            if type(outer) is not int or outer > 0: raise ValueError('Particle imports cannot depend on donor exports.')
            if outer < 0: item['OuterIndex'] = -include(-outer - 1) - 1
            keys = ('ObjectName', 'ClassName', 'ClassPackage', 'OuterIndex', 'PackageName')
            found = next((i for i, v in enumerate(target) if all(v.get(k) == item.get(k) for k in keys)), None)
            if found is None:
                if item.get('ClassName') == 'NiagaraSystem' and any(v.get('ObjectName') == item.get('ObjectName') for v in target):
                    raise ValueError('Ambiguous Niagara object name in the timeline shell.')
                found = len(target); target.append(item)
                for k in ('ObjectName', 'ClassName', 'ClassPackage', 'PackageName'):
                    if isinstance(item.get(k), str) and item[k] not in names: names.append(item[k])
            mapped[index] = found; visited.remove(index); return found
        include(reference['index'])


def patch_constants(value):
    """Remove seqdump's type annotations from bytecode field replacements."""
    if isinstance(value, dict):
        return {key: patch_constants(child) for key, child in value.items() if key != '$struct'}
    if isinstance(value, list): return [patch_constants(child) for child in value]
    return copy.deepcopy(value)


def build_effect_sequence(job, out, work, command, usmap, run):
    """Author normal motions/hits with imported native target effect references."""
    import ffbe_resonance
    path = Path(out) / (job['asset'] + '.uasset')
    dump = Path(work) / (path.stem + '-effects-authored.json')
    run([*command, 'tojson', str(path), str(dump), '--usmap', usmap])
    asset = json.loads(dump.read_text(encoding='utf-8-sig'))
    effect_imports(asset, job['effectImports'])
    # $struct belongs to seqdump's description, not the cooked struct's
    # fields. Keep actual constants and the tojson asset metadata intact.
    edits = [{**edit, 'set': patch_constants(edit['set'])}
             for edit in ffbe_resonance.author(asset, job['plan'])]
    dump.write_text(json.dumps(asset, ensure_ascii=False), encoding='utf-8')
    patch = dump.with_name(path.stem + '-effects-events.json')
    patch.write_text(json.dumps({'legacyRoot': str(out), 'outRoot': str(out),
        'sequenceData': [{'asset': job['asset'], 'json': str(dump)}],
        'bytecode': [{'asset': job['asset'], **e} for e in edits]}), encoding='utf-8')
    run([*command, 'patch', str(patch), '--usmap', usmap])
    verified = dump.with_name(path.stem + '-effects-verified.json')
    run([*command, 'seqdump', str(path), str(verified), '--usmap', usmap])
    actual = json.loads(verified.read_text(encoding='utf-8-sig'))
    written = dump.with_name(path.stem + '-effects-written.json')
    run([*command, 'tojson', str(path), str(written), '--usmap', usmap])
    written_imports = json.loads(written.read_text(encoding='utf-8-sig'))['Imports']
    functions = {k.split(':', 1)[0]: v for k, v in actual.items()}
    for edit in edits:
        if edit['set'].get('EventType') not in EFFECT_EVENTS: continue
        event = functions.get(str(edit['export']), {})
        try:
            if enum(event.get('EventType')) != edit['set']['EventType']: raise ValueError('The effect event type differs.')
            verify_particle_constants(edit['set'], event, written_imports)
        except ValueError as error:
            raise ValueError(f'The written skill timeline did not retain particle references: {error} Mod packing stopped.') from error


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
        steal_plan = steal_trial_plan(skill) if sid == 400260 and not recipe else None
        if sid in MONSTER_NEEDLES and not recipe:
            expected = ('Ability', 'Physic', 'Fixed', 'Single', 'Enemies')
            signature = tuple(enum(skill.get(k)) for k in ('skillAttrType', 'DamageType', 'damageCalcType', 'TargetType', 'defaultTargetRelation'))
            if signature != expected or skill.get('hitCount') != 1 or skill.get('magnification') != MONSTER_NEEDLES[sid][1]:
                raise ValueError('The monster Needle trial requires the original single-hit fixed-damage definition.')
            if not native or str(sid) not in native.visual_policy:
                raise ValueError('The monster Needle trial needs the prepared game catalog and native Needle effects.')
        profile_reason = None; visual_bundle = None
        if native and str(sid) in native.visual_policy and not recipe:
            try: visual_bundle = native.target_effects(sid)
            except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError, subprocess.SubprocessError) as error:
                # A mapped/labelled effect must not quietly become another
                # motion-only "success". Preserve the installed mod and report
                # exactly which donor could not be prepared.
                raise ValueError(f'Could not prepare effects for {native.names.get(sid, sid)} ({sid}): {error}') from error
        if not visual_bundle and sid in ANIMATION_PROFILES and not recipe:
            presentation, profile_reason = native.profile(sid, skill, owners, tables, clones) if native else (None, 'Native sequence audit unavailable.')
            if presentation:
                repaired.append(sid)
                coverage.append({'id': sid, 'status': 'animation_profile', **presentation}); continue
        donor, reason = native.reuse(sid, skill, tables, clones) if native and not visual_bundle and sid not in (400260, 400300) else (None, 'Native sequence audit unavailable.')
        if donor is not None:
            repaired.append(sid); reused.append((sid, donor))
            coverage.append({'id': sid, 'status': 'native_reuse', 'donor': donor}); continue
        if enum(skill.get('skillAttrType')) not in NORMAL_SKILLS:
            coverage.append({'id': sid, 'status': 'unresolved', 'reason': 'Specialized skill type.'}); continue
        magic = skill.get('skillAttrType', '').split('::')[-1] in ('Magic', 'MagicSword') or skill.get('DamageType', '').split('::')[-1] != 'Physic'
        if visual_bundle: magic = enum(skill.get('DamageType')) != 'Physic'
        hits = int(skill.get('hitCount') or 1)
        if not 0 < hits <= 30:
            coverage.append({'id': sid, 'status': 'unresolved', 'reason': 'Unsupported hit count.'}); continue
        import ffbe_resonance
        source = Path(root) / 'extracted/legacy' / (ffbe_resonance.SHELL + '.uasset')
        if not source.is_file(): extract('Sequencer/Battle/Skill/440110/440111/')
        if not source.is_file(): raise ValueError('The battle timeline template could not be extracted. Prepare the game files again.')
        plan = (steal_plan if steal_plan else barrage_trial_plan(root, owners, skill) if sid == 400300 and not recipe else
                ffbe_resonance.schedule(max(motion_seconds(u, root, magic) for u in owners), hits, sid, movement={'enabled': False}))
        plan['events'] = [e for e in plan['events'] if e['set']['EventType'] not in
                          ('PostSetDefaultColorGrading', 'PostSetColorGradingGlobalParameter', 'CameraSetDefault', 'OtherSetGameSpeed')]
        for event in plan['events']:
            st = event['set']
            if st['EventType'] == 'OtherReaction':
                # Ordinary actions need the engine's reaction-colour lifecycle.
                # The LB scheduler disables it; carrying that flag into a normal
                # action can strand a friendly target in its white hit state.
                # Keep the same reaction/hit rather than adding a cleanup hit.
                st['Otber_Reaction_bChangeColor'] = True
            if st.get('Unit_PlayAnimByName_AnimationName') == 'LB1': st['Unit_PlayAnimByName_AnimationName'] = 'magic_attack' if magic else 'attack_A'
            elif st.get('Unit_PlayAnimByName_AnimationName') == 'LB1_before': st['Unit_PlayAnimByName_AnimationName'] = 'magic_idle' if magic or enum(skill.get('skillAttrType')) == 'MagicSword' else 'command'
        if visual_bundle: add_target_effects(plan, visual_bundle)
        asset = f'FFRS/Content/Sequencer/Battle/Skill/{sid}/{sid+1}/SEQ_Battle_{sid+1}_Master'
        clones.append({'from': ffbe_resonance.SHELL, 'to': asset,
                       'rename': [['SEQ_Battle_440111_Cut_000', f'SEQ_Battle_{sid+1}_Master']]})
        jobs.append({'asset': asset, 'plan': plan, 'audio': None, 'kind': 'skill_effect' if visual_bundle else 'skill_motion',
                     **({'effectImports': visual_bundle['imports']} if visual_bundle else {})})
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
        if visual_bundle:
            native.bind_reaction_visuals(sid, visual_bundle, tables)
            coverage.append({'id': sid, 'status': 'effect_reuse', **{k: visual_bundle[k] for k in ('donor', 'donorName', 'rule', 'tier')},
                             'reactionRow': visual_bundle.get('reactionRow'),
                             'particleEvents': sum(p['set']['EventType'] == 'EffectSpawnNiagaraAtTarget' for p in visual_bundle['events'])})
        elif sid == 400300 and not recipe:
            coverage.append({'id': sid, 'status': 'ffbe_barrage_trial', 'sourceSkill': 200310})
        elif steal_plan:
            coverage.append({'id': sid, 'status': 'ffr_steal_motion_trial', 'sourceVision': 13118})
        else:
            coverage.append({'id': sid, 'status': 'motion_fallback', 'nativeReason': reason,
                             **({'profileReason': profile_reason} if profile_reason else {})})
    for entry in coverage:
        if entry['status'] == 'ffr_steal_motion_trial':
            print('  Steal FFR test: recipient approaches, uses its ready pose, resolves one original item theft, then returns to idle/position. Not a recovered Zidane-specific sequence.')
        elif entry['status'] == 'ffbe_barrage_trial':
            print('  Barrage FFBE test: four imported attack cycles with FFBE impact timing; original FFR damage, random targets and four hits retained.')
        elif entry['status'] == 'effect_reuse':
            print(f'  {entry["id"]}: target effects from {entry["donorName"]} ({entry["donor"]}); {entry["rule"]}, tier {entry["tier"]}; original mechanics retained.')
        elif entry['status'] == 'animation_profile':
            print(f'  {entry["profile"]}: audited visual profile from {entry["donor"]}; original mechanics retained.')
        elif entry.get('profileReason'):
            print(f'  {ANIMATION_PROFILES[entry["id"]]["name"]}: keeping motion fallback: {entry["profileReason"]}')
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
