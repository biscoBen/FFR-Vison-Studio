"""Local launch preparation: native comparisons, reversible presets and Studio backups.

Reports identify source data, never certify visual playback. Finished Deck snapshots
use _ffr_deck_sync's existing owned-file transaction and contain no editable config.
"""
import copy
import csv
import gzip
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor

import _ffr_deck_sync as transfer

HOME = 'launch-prep'
PREPARED = HOME + '/prepared-game.json'
STATE = HOME + '/state.json'
MAX_BACKUP = 32 * 1024**2
INPUTS = tuple('mods/EstherTsukiko/' + n for n in transfer.STUDIO_INPUTS)
TABLE_SCOPE = ('Datatable/Skill/', 'Datatable/Asset/Skill/', 'Datatable/Battle/Sequencer/',
               'Datatable/Unit/', 'Datatable/Item/Vision/', 'Datatable/Asset/Sound/',
               'Datatable/Battle/Unit/', 'Datatable/Asset/Battle/Unit/',
               'Datatable/Asset/Battle/Stage/', 'Datatable/Asset/Battle/AI/',
               'Datatable/Shop/DT_ShopList', 'Datatable/Shop/DT_VariousShopsList',
               'Datatable/Map/MapData/', 'Datatable/Map/CDT_MapData_',
               'Datatable/Asset/Map/DT_MapUnitAsset', 'Datatable/Asset/Map/DT_MapUnitPlacementAsset',
               'Datatable/Encount/DT_BattleGroup', 'Datatable/Event/TalkEvent/',
               'Datatable/Event/BattleEvent/DT_BtlCmnEventDataBundle',
               'Datatable/UI/Common/Dialog/DT_DIalogChoice',
               'Datatable/UI/Skill/', 'Datatable/UI/Vision/DT_VisionUpgrade_VisionUpgradeData',
               'Datatable/PostProcess/DT_ColorGradingParameter')
REFERENCE_SCOPE = (*TABLE_SCOPE, 'Sequencer/Battle/', 'Sequencer/Skill/')
_job = {'running': False, 'result': None, 'message': '', 'log': []}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


@lru_cache(maxsize=4)
def bundled(name):
    path = Path(__file__).with_name(name)
    return json.loads(gzip.decompress(path.read_bytes()) if name.endswith('.gz') else path.read_bytes())


def record(root, name, default=None):
    return transfer.read_json(transfer.checked(root, name), default)


def revision(root):
    return record(root, STATE, {}).get('revision', '')


def changed(root):
    transfer.json_write(transfer.checked(root, STATE), {'revision': uuid.uuid4().hex})
    transfer.begin_build(root)


def game(env):
    return Path(env['ffrenv'].game_root())


def native_identity(env):
    return transfer.game_identity(game(env))


def known_demo(identity):
    return identity == bundled('launch_demo.json.gz')['gameIdentity']


def prepared_status(env):
    root = Path(env['ROOT'])
    current = native_identity(env)
    saved = record(root, PREPARED, {})
    # Existing demo installations may be adopted only against the original
    # container identity AND exact prepared source-table hashes.
    if not saved and known_demo(current):
        baseline = bundled('launch_demo.json.gz')
        expected = baseline['adoptionRows']
        if expected and all(transfer.checked(root, p).is_file() and transfer.sha(transfer.checked(root, p)) == h
                            for p, h in expected.items()):
            saved = {'schema': 1, 'gameIdentity': current, 'source': 'Exact demo tables and containers'}
            transfer.json_write(transfer.checked(root, PREPARED), saved)
    ready = saved.get('gameIdentity') == current
    if ready: message = 'Prepared data matches this game build.'
    elif saved.get('source') == 'Preparation incomplete':
        message = 'The last optional preparation did not finish. You can retry it here; preparation status does not block builds.'
    elif not saved.get('gameIdentity'):
        message = 'No optional game-data baseline is recorded. Builds use the existing local data.'
    else:
        message = 'The selected game files differ from the optional preparation record. You can refresh the data here when needed.'
    return {'gameIdentity': current, 'prepared': ready,
            'label': 'Recognized demo build' if known_demo(current) else 'Selected game build',
            'message': message,
            'demoPatchReview': saved.get('demoPatchReview') == current['sha256']}


def brief(env):
    value = {'launchRevision': revision(env['ROOT'])}
    try: value['gameCompatibility'] = prepared_status(env)
    except (OSError, ValueError, transfer.SyncError):
        value['gameCompatibility'] = {'prepared': False, 'message': 'Optional game preparation status is unavailable.'}
    return value


def flags(root):
    import _ffr_ability_modes as ability
    import _ffr_sephira as sephira
    import _ffr_testing as testing
    a, s, t = ability.settings(root), sephira.settings(root), testing.settings(root)
    enabled = []
    if a['showUnverified'] and a['useChanges']: enabled.append('Use our skill changes')
    if a['showUnverified'] and a.get('useNativeRepairs'): enabled.append('Repair native skill bindings / motions')
    if s['useBorrowedSkillVisuals']: enabled.append('Use borrowed Sephira skill visuals')
    if s.get('shopAcquisitionOverride'): enabled.append('Sephira visions: 1-gil Mitra shop')
    roster = Path(root) / 'mods/EstherTsukiko/units.json'
    if roster.is_file():
        import _ffr_shrine_challenges as challenges
        units = [u for u in sephira.active_units(json.loads(roster.read_bytes())) if not sephira.shop_override(u,s)]
        if (challenges.plans(units) or any(challenges.route(u) == 'folka_shop' for u in units)):
            enabled.append('Sephira vision challenges and story shop')
    for key, label in (('ffbeNeedles', 'FFBE 1,000 Needles import'), ('practiceBattle', 'Shop practice battle'),
                       ('finaCinematic', 'Crystal Fina cinematic test'),
                       ('maxMr', 'One-battle MR'), ('crystalCave', 'Legacy Crystal Fina cave'),
                       ('crystalCaveTest', 'Legacy Crystal Fina test cave'), ('fieldLeader', 'Walking-character cycling')):
        if t[key]: enabled.append(label)
    return {'abilities': a, 'sephira': s, 'testing': t, 'enabledPatches': enabled}


def guard(env, installing=False):
    if _job['running']: raise ValueError('Wait for the launch collection or snapshot export to finish.')
    if env.get('setup_state', {}).get('running'):
        raise ValueError('Wait for the current game preparation to finish.')
    # Preparation and patch review are optional tools. A normal build reads no
    # preparation ledger and never launches a full extraction/table retry pass.
    status = {'gameIdentity': native_identity(env)}
    if installing:
        built = record(env['ROOT'], 'build/launch-game.json', {})
        if (built.get('gameIdentity') != status['gameIdentity']
                or built.get('inputsSha256') != transfer.inputs_digest(env['ROOT'])):
            raise ValueError('The last mod was built for different or untracked game data. Rebuild before installing.')
    return status


def capture_build(env, started=None):
    status = guard(env)
    status['inputsSha256'] = transfer.inputs_digest(env['ROOT'])
    if started and (status['gameIdentity'] != started['gameIdentity'] or status['inputsSha256'] != started['inputsSha256']):
        raise ValueError('Game or Studio inputs changed during the build. Rebuild before installing/exporting.')
    transfer.json_write(transfer.checked(env['ROOT'], 'build/launch-game.json'), status)


def busy(env):
    if (env.get('state', {}).get('running') or env.get('setup_state', {}).get('running')
            or transfer._publishing['running'] or _job['running']):
        raise ValueError('Wait for the current build, preparation or export to finish.')


def validate_inputs(files):
    import _ffr_ability_modes as ability
    import _ffr_sephira as sephira
    import _ffr_testing as testing
    if not isinstance(files, dict) or set(files) - set(INPUTS):
        raise ValueError('Unsupported Studio backup files.')
    for name, raw in files.items():
        value = json.loads(raw)
        if name.endswith('/units.json'):
            if not isinstance(value, list) or len(value) > 1024:
                raise ValueError('Invalid saved roster.')
            keys, ids = set(), set()
            for unit in value:
                if (not isinstance(unit, dict) or not isinstance(unit.get('key'), str)
                        or not re.fullmatch(r'[A-Za-z0-9_-]+', unit['key'])
                        or type(unit.get('id')) is not int or unit['id'] <= 0
                        or unit['key'] in keys or unit['id'] in ids):
                    raise ValueError('Saved roster has invalid or duplicate unit identities.')
                keys.add(unit['key']); ids.add(unit['id'])
        elif name.endswith('/ability-modes.json'): ability.validate(value)
        elif name.endswith('/sephira-settings.json'): sephira.validate_settings(value)
        elif name.endswith('/testing.json'): testing.validate_settings(value)
        elif not isinstance(value, dict): raise ValueError('Invalid icon layout.')
    return files


def input_bytes(root):
    return {p: transfer.checked(root, p).read_bytes() for p in INPUTS if transfer.checked(root, p).is_file()}


def backup(root, output):
    files = validate_inputs(input_bytes(root))
    if sum(map(len, files.values())) > MAX_BACKUP: raise ValueError('Studio settings exceed the backup size limit.')
    manifest = {'schema': 1, 'kind': 'ffr-studio-backup',
                'files': {k: {'sha256': hashlib.sha256(v).hexdigest(), 'size': len(v)} for k, v in files.items()}}
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('manifest.json', json.dumps(manifest))
        for name, value in files.items(): bundle.writestr(name, value)
    return manifest


def read_backup(raw):
    if len(raw) > MAX_BACKUP: raise ValueError('Choose a Studio backup ZIP smaller than 32 MiB.')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            names = bundle.namelist()
            if (len(names) != len(set(names)) or set(names) - {'manifest.json', *INPUTS}
                    or 'manifest.json' not in names or sum(p.file_size for p in bundle.infolist()) > MAX_BACKUP):
                raise ValueError('Invalid Studio backup members.')
            manifest = json.loads(bundle.read('manifest.json'))
            if manifest.get('schema') != 1 or manifest.get('kind') != 'ffr-studio-backup':
                raise ValueError('This is not a Studio backup. Finished Deck snapshots use the Deck installer.')
            if set(names) != {'manifest.json', *manifest['files']}:
                raise ValueError('Studio backup file list differs from its manifest.')
            files = {name: bundle.read(name) for name in manifest['files']}
            for name, value in files.items():
                info = bundle.getinfo(name)
                if info.external_attr >> 16 & 0o170000 == 0o120000:
                    raise ValueError('Links are not permitted in a Studio backup.')
                if manifest['files'][name] != {'sha256': hashlib.sha256(value).hexdigest(), 'size': len(value)}:
                    raise ValueError('Studio backup checksum mismatch.')
            return validate_inputs(files)
    except (zipfile.BadZipFile, KeyError, TypeError) as error:
        raise ValueError('Invalid Studio backup ZIP.') from error


def replace_inputs(root, files):
    """Small explicit config set only; rollback all writes on any failure."""
    validate_inputs(files)
    previous = input_bytes(root)
    destination = transfer.checked(root, HOME + '/backups/' + uuid.uuid4().hex + '.zip')
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup(root, destination)
    try:
        for name in INPUTS:
            if name in files: transfer.atomic(transfer.checked(root, name), files[name])
            else: transfer.checked(root, name).unlink(missing_ok=True)
        changed(root)
    except BaseException:
        for name in INPUTS:
            if name in previous: transfer.atomic(transfer.checked(root, name), previous[name])
            else: transfer.checked(root, name).unlink(missing_ok=True)
        raise
    return destination.name


def original_preset(root):
    import _ffr_testing as testing
    files = input_bytes(root)
    options = testing.settings(root)
    options.update({key: False for key in ('maxMr', 'practiceBattle', 'surviveAtOne', 'ffbeNeedles', 'finaCinematic',
                                           'fieldLeader', 'crystalCave', 'crystalCaveTest')})
    files['mods/EstherTsukiko/testing.json'] = json.dumps(options).encode()
    files['mods/EstherTsukiko/ability-modes.json'] = json.dumps(
        {'schema': 1, 'showUnverified': True, 'useChanges': False, 'useNativeRepairs': False}).encode()
    files['mods/EstherTsukiko/sephira-settings.json'] = json.dumps(
        {'schema': 1, 'useBorrowedSkillVisuals': False}).encode()
    # Acquiring originals is also a testing intervention. Preserve every kit.
    if 'mods/EstherTsukiko/units.json' in files:
        units = json.loads(files['mods/EstherTsukiko/units.json'])
        for unit in units:
            if unit.get('testAcquire'): unit['testAcquire'] = False
        files['mods/EstherTsukiko/units.json'] = json.dumps(units, ensure_ascii=False).encode()
    return replace_inputs(root, files)


def canonical_asset(value):
    value = value.replace('\\', '/').strip().lstrip('\ufeff')
    if value.startswith('/Game/'): value = 'FFRS/Content/' + value[6:]
    value = value.removeprefix('../../../')
    return value


def summarize(root, identity, catalog=None):
    """Only source rows and source inventory; never a mod's generated output."""
    root = Path(root)
    tables = {}
    for path in sorted((root / 'extracted/rows').rglob('*.json')):
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        relative = canonical_asset(value.get('_asset', ''))
        if '/' not in relative: relative = ''
        if not relative: relative = path.relative_to(root / 'extracted/rows').as_posix()[:-5]
        relative = relative.removesuffix('.uasset').removeprefix('FFRS/Content/Datatable/')
        rows = value.get('rows')
        if not isinstance(rows, dict): continue
        field_types = {key: sorted({type(row[key]).__name__ for row in rows.values() if key in row})
                       for key in sorted({key for row in rows.values() for key in row})}
        tables[relative] = {'schemaSha256': digest({'rowStruct': value.get('_rowStruct'), 'fieldTypes': field_types}),
                            'fieldTypes': field_types,
                            'rows': {name: {'sha256': digest(row), 'id': row.get('ID', row.get('SkillId'))}
                                     for name, row in rows.items()}}
    inventory = []
    listing = root / 'extracted/utoc_filelist.tsv'
    if listing.is_file():
        for line in listing.read_text(encoding='utf-8-sig').splitlines():
            match = re.search(r'(?:\.\./){3}[^\r\n]+|(?:FFRS|Engine)/[^\t\r\n]+', line)
            if match: inventory.append(canonical_asset(match.group().split('\t')[0]))
    paths = set(inventory)
    timelines = {}
    legacy = root / 'extracted/legacy'
    for path in sorted(legacy.rglob('*')):
        if path.is_file() and '/Sequencer/' in path.as_posix() and path.suffix in ('.uasset', '.uexp'):
            timelines[path.relative_to(legacy).as_posix()] = transfer.sha(path)
    raw_skills = {}
    assets = {}
    links = {}
    route_tables = {}
    for path in (root / 'extracted/rows').rglob('*.json'):
        name = path.stem
        if name not in ('DT_SkillData', 'DT_SkillAsset', 'DT_SkillAsset_Prod',
                        'DT_SkillLinkSequencerData', 'CDT_SkillAsset_Demo', 'CDT_SkillAsset_Prod'): continue
        rows = json.loads(path.read_text(encoding='utf-8-sig')).get('rows', {})
        if name == 'DT_SkillData': raw_skills = {str(r['ID']): r for r in rows.values()}
        elif name == 'DT_SkillLinkSequencerData': links = {str(r['SkillId']): r for r in rows.values()}
        else: route_tables[name] = rows
    # Read the authoritative composite when available, including production-only
    # routes. The same binding in parent and composite is one route.
    if 'CDT_SkillAsset_Prod' in route_tables: native = [route_tables['CDT_SkillAsset_Prod']]
    elif 'CDT_SkillAsset_Demo' in route_tables: native = [route_tables['CDT_SkillAsset_Demo']]
    else: native = list(route_tables.values())
    for table in native:
        for r in table.values(): assets.setdefault(str(r['ID']), {})[digest(r)] = r
    names = {str(s['id']): s.get('name') for s in (catalog or {}).get('skills', [])}
    skills = {}
    for sid, row in raw_skills.items():
        candidates = {str(int(sid) + off) for off in (0, 1, 2)}
        for key in ('playSequencerId', 'sequencerIdWhenTargetFriendlies'):
            if type(row.get(key)) is int and row[key] > 0: candidates.add(str(row[key]))
        candidates.update(str(v) for k, v in links.get(sid, {}).items() if k != 'SkillId' and type(v) is int and v > 0)
        routes = sorted([r for key in sorted(candidates) for r in assets.get(key, {}).values()], key=digest)
        skills[sid] = {'name': names.get(sid), 'definitionSha256': digest(row), 'routes': routes,
                       'referencedSequenceAssets': {canonical_asset(r[k]).split('.')[0] + '.uasset':
                                                   canonical_asset(r[k]).split('.')[0] + '.uasset' in paths
                                                   for r in routes for k in ('LevelSequence', 'soundSequence') if r.get(k)},
                       'secondaryLink': links.get(sid)}
    return {'schema': 1, 'kind': 'ffr-native-reference', 'gameIdentity': identity, 'tables': tables,
            'skills': skills, 'inventory': sorted(paths), 'timelineFiles': timelines,
            'inGameValidated': False, 'scope': 'Native source tables, routing, timeline bytes and asset inventory. '
            'Presence and changed bytes do not prove visual, sound or aiming behavior.'}


def compare(before, after):
    if (not isinstance(before, dict) or not isinstance(after, dict)
            or before.get('kind') != 'ffr-native-reference' or after.get('kind') != 'ffr-native-reference'
            or any(not isinstance(x.get('tables'), dict) or not isinstance(x.get('skills'), dict)
                   or not isinstance(x.get('inventory'), list) or not isinstance(x.get('gameIdentity'), dict) for x in (before, after))):
        raise ValueError('Choose a native reference JSON exported by Launch preparation.')
    tables = {}
    for name in sorted(set(before['tables']) | set(after['tables'])):
        a, b = before['tables'].get(name, {}), after['tables'].get(name, {})
        ar, br = a.get('rows', {}), b.get('rows', {})
        added, removed = sorted(set(br)-set(ar)), sorted(set(ar)-set(br))
        edits = sorted(k for k in set(ar)&set(br) if ar[k] != br[k])
        if added or removed or edits or a.get('schemaSha256') != b.get('schemaSha256'):
            tables[name] = {'added': added, 'removed': removed, 'changed': edits,
                            'schemaChanged': a.get('schemaSha256') != b.get('schemaSha256')}
    a, b = before.get('inventory', []), after.get('inventory', [])
    def skill_record(record):
        value = {k: v for k, v in (record or {}).items() if k != 'name'}
        if 'routes' in value:
            value['routes'] = sorted({digest(r) for r in value['routes']})
        return value
    skills = {sid: {'before': before.get('skills', {}).get(sid), 'after': after.get('skills', {}).get(sid)}
              for sid in sorted(set(before.get('skills', {})) | set(after.get('skills', {})))
              if skill_record(before.get('skills', {}).get(sid)) != skill_record(after.get('skills', {}).get(sid))}
    old, new = before.get('timelineFiles', {}), after.get('timelineFiles', {})
    return {'schema': 1, 'before': before['gameIdentity'], 'after': after['gameIdentity'],
            'tables': tables, 'skills': skills,
            'assetsAdded': sorted(set(b)-set(a)), 'assetsRemoved': sorted(set(a)-set(b)),
            'timelinesChanged': sorted(k for k in set(old)&set(new) if old[k] != new[k]),
            'inGameValidated': False}


def run(command, log):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        # Keep the exception's leading cause as well as its last stack frames.
        if len(detail) > 1400: detail = detail[:800] + '\n...\n' + detail[-600:]
        raise ValueError('Native reference command failed: ' + detail)
    if result.stdout: log(result.stdout[-300:])
    return result.stdout


def collect(env, log):
    """Fresh read-only source view excludes every ~mods file."""
    root, source = Path(env['ROOT']), game(env)
    tool = env['ffrenv']
    mapping = Path(tool.USMAP)
    if not mapping.is_file():
        raise ValueError('The mappings file is unavailable: ' + str(mapping) + '. Prepare the selected game first.')
    identity = native_identity(env)
    destination = transfer.checked(root, HOME + '/references/' + uuid.uuid4().hex)
    destination.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='ffr-native-view-') as folder:
        view = Path(folder)
        for path in (source / 'FFRS/Content/Paks').iterdir():
            if path.is_file() and path.suffix.lower() in ('.utoc', '.ucas', '.pak'):
                transfer.checked(source / 'FFRS/Content/Paks', path.name)
                try: os.link(path, view / path.name)
                except OSError:
                    log('Copying official container for an isolated read-only view: ' + path.name)
                    shutil.copy2(path, view / path.name)
        listing = run([tool.RETOC, 'list', '--path', view], log)
        transfer.atomic(destination / 'extracted/utoc_filelist.tsv', listing.encode())
        for scope in REFERENCE_SCOPE:
            log('Reading ' + scope)
            run([tool.RETOC, 'to-legacy', '--no-shaders', '--filter', scope, view,
                 destination / 'extracted/legacy'], log)
    legacy = destination / 'extracted/legacy/FFRS/Content/Datatable'
    jobs = list(legacy.rglob('*.uasset'))
    if not jobs: raise ValueError('The fresh game reference contains no readable tables.')
    def dump(path, usmap):
        relative = path.relative_to(legacy).with_suffix('.json')
        out = destination / 'extracted/rows' / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        try: run([*tool.FFRDT, 'rows', path, out, '--usmap', usmap], lambda _: None)
        except ValueError as error: raise ValueError('Could not decode ' + relative.as_posix() + ': ' + str(error)) from error
        json.loads(out.read_text(encoding='utf-8-sig'))
        log('Decoded ' + relative.as_posix())
    # UAssetAPI opens a .usmap with exclusive sharing. Separate copies let the
    # parallel readers run without competing for the same mappings file.
    with tempfile.TemporaryDirectory(prefix='ffr-reference-maps-') as folder:
        maps = [Path(folder) / (str(i) + '.usmap') for i in range(4)]
        for path in maps: shutil.copyfile(mapping, path)
        log('Decoding ' + str(len(jobs)) + ' native tables with separate mappings files...')
        # Initialize the single-file reader before starting the parallel pass.
        dump(jobs[0], maps[0])
        remaining = jobs[1:]
        def batch(index):
            for path in remaining[index::4]: dump(path, maps[index])
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(batch, range(4)))
    if native_identity(env) != identity: raise ValueError('Game updated during collection. Collect again after the update finishes.')
    result = summarize(destination, identity)
    transfer.json_write(destination / 'reference.json', result)
    delta = compare(bundled('launch_demo.json.gz'), result)
    transfer.json_write(destination / 'comparison.json', delta)
    transfer.json_write(transfer.checked(root, HOME + '/latest-reference.json'), {'folder': destination.name})
    log('Reference complete. Source presence is separate from live-game verification.')
    return {'folder': destination.name, 'changedTables': len(delta['tables']), 'changedSkills': len(delta['skills']),
            'addedAssets': len(delta['assetsAdded']), 'removedAssets': len(delta['assetsRemoved'])}


def prepare_rows(setup, env, log):
    """Optional refresh: skip text tables and cache unsupported optional reads."""
    legacy = Path(setup.LEGACY) / 'FFRS/Content/Datatable'
    destination = Path(setup.ROWS)
    required = {name.replace('\\', '/') for name in setup.REQUIRED_TABLES}
    tool = setup.ffrenv
    mapping = Path(tool.USMAP)
    reader = [(str(part), Path(part).stat().st_size, Path(part).stat().st_mtime_ns)
              for part in tool.FFRDT if Path(part).is_file()]
    signature = {'game': native_identity(env), 'mapping': transfer.sha(mapping),
                 'reader': digest([list(map(str, tool.FFRDT)), reader])}
    cache_path = HOME + '/optional-table-reads.json'
    try: previous = record(env['ROOT'], cache_path, {})
    except transfer.SyncError: previous = {}
    if not isinstance(previous, dict): previous = {}
    cached = previous.get('failures', {}) if previous.get('schema') == 2 and previous.get('signature') == signature else {}
    cached = {key: entry for key, entry in cached.items() if isinstance(entry, dict)} if isinstance(cached, dict) else {}
    jobs, failures, source_hashes = [], {}, {}
    strings = skipped = 0
    for path in sorted(legacy.rglob('*.uasset')):
        relative = path.relative_to(legacy).with_suffix('')
        key = relative.as_posix()
        # The catalog gets localized names from locres_en.json. These string
        # packages are not inputs to the table builder or its required set.
        if relative.parts[0].casefold() == 'strings' and key not in required:
            strings += 1; continue
        out = destination / relative.with_suffix('.json')
        if out.is_file(): continue
        source_hashes[key] = digest({suffix: transfer.sha(path.with_suffix(suffix))
                                    for suffix in ('.uasset', '.uexp') if path.with_suffix(suffix).is_file()})
        if key not in required and cached.get(key, {}).get('source') == source_hashes[key]:
            failures[key] = cached[key]; skipped += 1; continue
        jobs.append((path, out, key))
    if strings: log(f'  skipped {strings} localization string tables; Studio uses the text catalog')
    if skipped: log(f'  skipped {skipped} unchanged unsupported optional tables')
    errors = {}; progress = 0; lock = threading.Lock()
    def one(job, usmap):
        nonlocal progress
        path, out, key = job
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run([*tool.FFRDT, 'rows', str(path), str(out), '--usmap', str(usmap)],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode or not out.is_file():
                raise ValueError((result.stderr or result.stdout or f'exit {result.returncode}').strip()[:900])
            document = json.loads(out.read_text(encoding='utf-8-sig'))
            if not isinstance(document, dict) or not isinstance(document.get('rows'), dict):
                raise ValueError('The reader did not export a table.')
            errors.pop(key, None)
        except (OSError, ValueError) as error:
            out.unlink(missing_ok=True)
            errors[key] = str(error)
        with lock:
            progress += 1
            if progress % 100 == 0: log(f'  {progress}/{len(jobs)} tables')
    if jobs:
        log(f'reading {len(jobs)} data tables with separate mappings files ...')
        with tempfile.TemporaryDirectory(prefix='ffr-setup-maps-') as folder:
            maps = [Path(folder) / (str(index) + '.usmap') for index in range(4)]
            for path in maps: shutil.copyfile(mapping, path)
            one(jobs[0], maps[0])  # Warm up the single-file .NET reader once.
            def batch(index):
                for job in jobs[1:][index::4]: one(job, maps[index])
            with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(batch, range(4)))
            retry = [job for job in jobs if job[2] in required and job[2] in errors]
            if retry:
                log(f'  retrying {len(retry)} required table(s) ...')
                for job in retry: one(job, maps[0])
    uncached = 0
    for key, error in errors.items():
        if key in required: log(f'  ! needed table failed: {key}: {error}')
        elif any(marker in error.casefold() for marker in ('did not export a table', 'not a datatable',
                  'no datatable export', 'unsupported property', 'unsupported export')):
            failures[key] = {'source': source_hashes[key], 'error': error}
        else:
            uncached += 1
            log(f'  optional table read failed: {key}: {error}')
    if failures: log(f'  {len(failures)} unsupported optional table(s) omitted; unchanged failures will not be retried')
    if uncached: log(f'  {uncached} other optional read failure(s) will be tried again on the next refresh')
    transfer.json_write(transfer.checked(env['ROOT'], cache_path),
                        {'schema': 2, 'signature': signature, 'failures': failures})


def prepare_game(selected, setup, env, log):
    """Quarantine stale derived game data; never reuse shipped demo rows/catalog."""
    root = Path(env['ROOT'])
    identity = transfer.game_identity(selected)
    previous = record(root, PREPARED, {})
    if previous.get('gameIdentity') != identity:
        # Invalidate before moving anything. A failed preparation must not let
        # switching back to the previous game reuse partial newer-game files.
        transfer.json_write(transfer.checked(root, PREPARED),
                            {'schema': 1, 'source': 'Preparation incomplete', 'requestedGameIdentity': identity})
        folder = transfer.checked(root, HOME + '/prepared-backups/' + uuid.uuid4().hex)
        folder.mkdir(parents=True)
        moved = []
        # All extracted packages are version-dependent, including Fina donors.
        for relative in ('extracted', 'build'):
            source = transfer.checked(root, relative)
            if source.exists():
                source.rename(folder / relative); moved.append(relative)
        transfer.json_write(folder / 'state.json', {'previous': previous, 'moved': moved})
        log('Preserved prior prepared data in ' + str(folder))
    shipped = setup.SHIPPED
    filters = setup.EXTRACT_FILTERS
    listing = setup._listing
    dump_rows = getattr(setup, '_dump_rows', None)
    try:
        # Mapping/enums and FFBE data remain pinned helpers. Native source rows,
        # native listing and catalog must be rebuilt from this installation.
        setup.SHIPPED = [(a, b) for a, b in shipped if a not in ('ffr_catalog.json', 'utoc_filelist.tsv', 'DA_UIUnitSsLayout.json')]
        if dump_rows is not None: setup._dump_rows = lambda output: prepare_rows(setup, env, output)
        with tempfile.TemporaryDirectory(prefix='ffr-prepare-view-') as folder:
            view = Path(folder)
            paks = Path(selected) / 'FFRS/Content/Paks'
            for path in paks.iterdir():
                if path.is_file() and path.suffix.lower() in ('.utoc', '.ucas', '.pak'):
                    transfer.checked(paks, path.name)
                    try: os.link(path, view / path.name)
                    except OSError: shutil.copy2(path, view / path.name)
            extract = setup._extract
            setup._extract = lambda _paks, output: extract(str(view), output)
            # Use retoc directly rather than the demo-specific shipped listing.
            def fresh_listing(_paks, output):
                text = run([env['ffrenv'].RETOC, 'list', '--path', view], output)
                # ffr_catalog expects chunk-id<TAB>path, not retoc's columns.
                rows = []
                for line in text.splitlines():
                    match = re.search(r'(?:\.\./){3}[^\r\n]+', line)
                    if match: rows.append('native\t' + match.group())
                if not rows: raise ValueError('The native container inventory could not be read.')
                transfer.atomic(root / 'extracted/utoc_filelist.tsv', ('\n'.join(rows)+'\n').encode())
            setup._listing = fresh_listing
            setup.prepare(str(selected), log=log)
        if transfer.game_identity(selected) != identity: raise ValueError('Game changed during preparation. Prepare it again.')
        # Clear in-memory catalog overlays, which depend on the old game tables.
        catalog = env.get('ffr_catalog')
        if catalog:
            for name in ('_cache', '_catalog', '_rows_cache'):
                if hasattr(catalog, name): setattr(catalog, name, None if name != '_rows_cache' else {})
        transfer.json_write(transfer.checked(root, PREPARED), {'schema': 1, 'gameIdentity': identity,
                           'source': 'Fresh official game tables and inventory'})
        changed(root)
    finally:
        setup.SHIPPED, setup.EXTRACT_FILTERS, setup._listing = shipped, filters, listing
        if dump_rows is not None: setup._dump_rows = dump_rows
        if 'extract' in locals(): setup._extract = extract


def results_path(env):
    return HOME + '/tests/' + native_identity(env)['sha256'] + '.json'


def results(env):
    return record(env['ROOT'], results_path(env), {'schema': 1, 'gameIdentity': native_identity(env), 'observations': {}})


def csv_sheet(env):
    data = results(env)['observations']
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    writer.writerow(('Test', 'Skill IDs', 'Enemy/source', 'Demo evidence', 'Visuals', 'Direction', 'Sound', 'Hit timing', 'Notes', 'Game fingerprint'))
    for item in bundled('launch_tests.json')['tests']:
        saved = data.get(item['key'], {})
        values = (item['name'], '/'.join(map(str, item.get('skillIds', []))), item.get('source', ''), item.get('demo', ''),
                  *(saved.get(k, 'untested') for k in ('visuals', 'direction', 'sound', 'timing')), saved.get('notes', ''), native_identity(env)['sha256'])
        writer.writerow(["'"+v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v for v in values])
    return out.getvalue()


def register(app, env):
    from fastapi import HTTPException, Request
    from fastapi.responses import FileResponse, Response, JSONResponse
    from starlette.background import BackgroundTask
    globals()['Request'] = Request
    root = Path(env['ROOT'])
    native_env = env['ffrenv']
    if not getattr(native_env, '_launch_detection_installed', False):
        original_detect = native_env.detect_game
        def detect():
            selected = original_detect()
            if selected: return selected
            for library in native_env.steam_libraries():
                common = Path(library) / 'steamapps/common'
                if common.is_dir():
                    found = sorted(p for p in common.iterdir() if p.is_dir() and (p / transfer.MARKER).is_file())
                    if found: return str(found[0])
            return None
        native_env.detect_game = detect
        native_env._launch_detection_installed = True

    @app.middleware('http')
    async def preserve_job_inputs(request, call_next):
        path = request.url.path
        expected = request.headers.get('X-Launch-Revision')
        if (path == '/api/spec' and request.method == 'PUT' and expected is not None and expected != revision(root)):
            return JSONResponse({'detail': 'A snapshot or preset replaced the saved setup. Reload the restored setup before saving these edits.'}, status_code=409)
        if (_job['running'] and request.method in ('POST', 'PUT', 'DELETE')
                and (path.startswith('/api/spec') or path in ('/api/setup', '/api/build', '/api/install',
                     '/api/testing', '/api/abilities/settings', '/api/sephira/settings', '/api/deck/publish'))):
            return JSONResponse({'detail': 'Wait for the launch collection or snapshot export to finish.'}, status_code=409)
        return await call_next(request)

    def checked_call(action):
        with transfer._operation:
            try: return action()
            except (OSError, ValueError, transfer.SyncError) as error: raise HTTPException(409, str(error)) from error

    def download(action, filename):
        busy(env)
        fd, name = tempfile.mkstemp(prefix='ffr-launch-', suffix='.zip')
        os.close(fd)
        try: action(Path(name))
        except BaseException:
            Path(name).unlink(missing_ok=True); raise
        return FileResponse(name, media_type='application/zip', filename=filename,
                            background=BackgroundTask(lambda: Path(name).unlink(missing_ok=True)))

    @app.get('/launch-preparation')
    def page(): return FileResponse(Path(__file__).with_name('launch_prep.html'), media_type='text/html')

    @app.get('/api/launch/status')
    def status():
        def value():
            return {**prepared_status(env), 'flags': flags(root), 'revision': revision(root),
                    'inputsSha256': transfer.inputs_digest(root), 'job': copy.deepcopy(_job),
                    'selectedGame': str(game(env)), 'preparing': copy.deepcopy(env.get('setup_state', {})),
                    'tests': bundled('launch_tests.json')['tests'], 'results': results(env),
                    'backupNames': sorted(p.name for p in (root / HOME / 'backups').glob('*.zip')),
                    'deckReady': transfer.checked(root, transfer.VERIFIED).is_file(),
                    'latestReference': record(root, HOME + '/latest-reference.json')}
        return checked_call(value)

    @app.get('/api/launch/studio-backup')
    def export_backup(): return checked_call(lambda: download(lambda p: backup(root, p), 'Studio-Backup.zip'))

    @app.get('/api/launch/deck-snapshot')
    def export_deck():
        def action():
            guard(env, installing=True)
            return download(lambda p: transfer.local_snapshot(env, p), 'Resonance-Mod-Snapshot.zip')
        return checked_call(action)

    @app.post('/api/launch/deck-export')
    def prepare_deck_export():
        def start():
            busy(env)
            guard(env, installing=True)
            identity = uuid.uuid4().hex
            _job.update(running=True, kind='snapshot', result=None, summary=None, download=None,
                        message='Packing a local Deck snapshot...', log=[])
            def worker():
                path = transfer.checked(root, HOME + '/exports/' + identity + '.zip')
                path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    transfer.local_snapshot(env, path)
                    for old in path.parent.glob('*.zip'):
                        if old != path: old.unlink(missing_ok=True)
                    _job.update(result='ok', message='Snapshot ready to download.', download=identity)
                except Exception as error:
                    path.unlink(missing_ok=True)
                    _job.update(result='failed', message=str(error))
                finally: _job['running'] = False
            threading.Thread(target=worker, daemon=True).start()
            return {'ok': True}
        return checked_call(start)

    @app.get('/api/launch/exports/{identity}')
    def ready_deck_export(identity: str):
        if not re.fullmatch(r'[0-9a-f]{32}', identity): raise HTTPException(404)
        path = transfer.checked(root, HOME + '/exports/' + identity + '.zip')
        if not path.is_file() or _job['running']: raise HTTPException(404)
        return FileResponse(path, media_type='application/zip', filename='Resonance-Mod-Snapshot.zip')

    @app.get('/api/launch/backups/{name}')
    def previous_backup(name: str):
        if not re.fullmatch(r'[0-9a-f]{32}\.zip', name): raise HTTPException(404)
        path = transfer.checked(root, HOME + '/backups/' + name)
        if not path.is_file(): raise HTTPException(404)
        return FileResponse(path, media_type='application/zip', filename='Studio-Backup-' + name)

    @app.post('/api/launch/backup/preview')
    async def preview(req: Request):
        raw = await limited(req)
        def action():
            files = read_backup(raw)
            units = json.loads(files.get('mods/EstherTsukiko/units.json', b'[]'))
            return {'units': [u.get('en', u['key']) for u in units], 'files': list(files),
                    'inputsSha256': transfer.inputs_digest(root), 'sha256': hashlib.sha256(raw).hexdigest()}
        return checked_call(action)

    @app.post('/api/launch/backup/restore')
    async def restore(req: Request):
        raw = await limited(req)
        def action():
            busy(env)
            if req.headers.get('if-match') != transfer.inputs_digest(root):
                raise ValueError('Studio settings changed after preview. Preview the backup again before restoring.')
            saved = replace_inputs(root, read_backup(raw))
            return {'ok': True, 'backup': saved, 'revision': revision(root)}
        return checked_call(action)

    async def limited(req):
        data = bytearray()
        async for chunk in req.stream():
            data.extend(chunk)
            if len(data) > MAX_BACKUP: raise HTTPException(413, 'Studio backup is larger than 32 MiB.')
        return bytes(data)

    @app.post('/api/launch/preset')
    def preset():
        def action():
            busy(env)
            return {'backup': original_preset(root), 'revision': revision(root)}
        return checked_call(action)

    @app.post('/api/launch/review-patches')
    def review(body: dict):
        def action():
            busy(env)
            status = prepared_status(env)
            if body.get('gameSha256') != status['gameIdentity']['sha256']:
                raise ValueError('The selected game changed. Refresh before recording the optional review.')
            saved = record(root, PREPARED, {})
            transfer.json_write(transfer.checked(root, PREPARED), {**saved, 'schema': 1, 'demoPatchReview': body['gameSha256']})
            return {'ok': True}
        return checked_call(action)

    @app.post('/api/launch/tests')
    def save_results(body: dict):
        def action():
            allowed = {x['key'] for x in bundled('launch_tests.json')['tests']}
            if body.get('gameSha256') != native_identity(env)['sha256']:
                raise ValueError('Game changed while editing results. Reload the page.')
            observed = body.get('observations')
            if not isinstance(observed, dict) or set(observed) - allowed: raise ValueError('Unknown test entries.')
            for value in observed.values():
                if (not isinstance(value, dict) or set(value) - {'visuals', 'direction', 'sound', 'timing', 'notes'}
                        or any(value.get(k, 'untested') not in ('untested', 'pass', 'fail', 'not-applicable') for k in ('visuals','direction','sound','timing'))
                        or not isinstance(value.get('notes', ''), str) or len(value.get('notes', '')) > 2000):
                    raise ValueError('Invalid test results.')
            transfer.json_write(transfer.checked(root, results_path(env)),
                                {'schema': 1, 'gameIdentity': native_identity(env), 'observations': observed})
            return {'ok': True}
        return checked_call(action)

    @app.get('/api/launch/tests.csv')
    def sheet(): return checked_call(lambda: Response(csv_sheet(env).encode('utf-8-sig'), media_type='text/csv',
                                  headers={'Content-Disposition': 'attachment; filename="Launch-Test-Sheet.csv"'}))

    @app.post('/api/launch/collect')
    def collection():
        def start():
            busy(env)
            _job.update(running=True, kind='reference', result=None, summary=None, download=None, message='Collecting fresh official game references...', log=[])
            def worker():
                try:
                    summary = collect(env, lambda line: _job['log'].append(str(line)))
                    _job.update(result='ok', message='Reference ready.', summary=summary)
                except Exception as error: _job.update(result='failed', message=str(error))
                finally: _job['running'] = False
            threading.Thread(target=worker, daemon=True).start()
            return {'ok': True}
        return checked_call(start)

    @app.get('/api/launch/reference')
    def reference():
        def action():
            latest = record(root, HOME + '/latest-reference.json', {})
            folder = latest.get('folder', '')
            if not re.fullmatch(r'[0-9a-f]{32}', folder): raise ValueError('Collect a reference first.')
            source = transfer.checked(root, HOME + '/references/' + folder)
            def pack(output):
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as bundle:
                    for path in sorted(source.rglob('*')):
                        if path.is_file(): bundle.write(path, path.relative_to(source).as_posix())
            return download(pack, 'Resonance-Native-Reference.zip')
        return checked_call(action)

    @app.post('/api/launch/compare')
    async def comparison(req: Request):
        raw = await limited(req)
        def action():
            incoming = json.loads(raw)
            baseline = bundled('launch_demo.json.gz')
            return compare(baseline, incoming)
        return checked_call(action)

    @app.get('/api/launch/demo-reference')
    def demo_reference():
        return Response(json.dumps(bundled('launch_demo.json.gz')), media_type='application/json',
                        headers={'Content-Disposition': 'attachment; filename="Demo-Native-Reference.json"'})
