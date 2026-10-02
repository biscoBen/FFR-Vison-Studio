#!/usr/bin/env python3
"""Audit every catalog entry against prepared game timelines without building a mod."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


def scheduled_keys(asset, functions):
    """Read enabled event tracks, keeping each cooked function/export binding."""
    exports = asset['Exports']; imports = asset['Imports']
    def prop(value, name):
        return next((p for p in value.get('Data', []) if p.get('Name') == name), {})
    def number(value):
        for _ in range(8):
            if isinstance(value, (int, float)) and not isinstance(value, bool): return int(value)
            if isinstance(value, dict): value = value.get('Value')
            elif isinstance(value, list) and value: value = value[0]
            else: return None
    functions = {int(k.split(':', 1)[0]): (k.split(':', 1)[1], v) for k, v in functions.items()}
    keys = []
    for track in exports:
        index = track.get('ClassIndex', 0)
        if index >= 0 or imports[-index-1]['ObjectName'] != 'MovieSceneEventTrack': continue
        if prop(track, 'bIsEvalDisabled').get('Value'): continue
        for ref in prop(track, 'Sections').get('Value', []):
            section = exports[(ref['Value'] if isinstance(ref, dict) else ref)-1]
            channel = prop(section, 'EventChannel').get('Value', [])
            values = {p['Name']: p['Value'] for p in channel}
            for i, key in enumerate(values.get('KeyValues', [])):
                pointers = next((p['Value'] for p in key['Value'] if p['Name'] == 'Ptrs'), [])
                fn = next((p['Value'] for p in pointers if p['Name'] == 'Function'), None)
                if fn in functions:
                    name, event = functions[fn]
                    keys.append((number(values['KeyTimes'][i]), event.get('EventType'), name))
    return sorted(keys)


class DecoderCache:
    def __init__(self, command, mapping, directory):
        self.command = command; self.mapping = Path(mapping); self.directory = Path(directory)
        self.contract = hashlib.sha256(self.mapping.read_bytes() + Path(command[-1]).read_bytes()).digest()

    def paths(self, source):
        source = Path(source)
        digest = hashlib.sha256(self.contract + source.read_bytes() + source.with_suffix('.uexp').read_bytes()).hexdigest()
        root = self.directory / digest
        return root / 'tojson.json', root / 'seqdump.json'

    def dumps(self, source):
        paths = self.paths(source); paths[0].parent.mkdir(parents=True, exist_ok=True)
        for verb, destination in zip(('tojson', 'seqdump'), paths):
            if not destination.exists():
                result = subprocess.run([*self.command, verb, str(source), str(destination),
                                         '--usmap', str(self.mapping)], capture_output=True, text=True, timeout=120)
                if result.returncode:
                    destination.unlink(missing_ok=True)
                    raise ValueError(f'{Path(source).name}: {verb} failed: {result.stderr or result.stdout}')
        return tuple(json.loads(p.read_text(encoding='utf-8-sig')) for p in paths)


def audit_catalog(native):
    """Report mapped failures together; retain unresolved and native entries."""
    records = []
    for skill in native.catalog.get('skills', []):
        sid = skill['id']; mapping = native.visual_policy.get(str(sid))
        record = {'id': sid, 'name': skill.get('name'), 'description': skill.get('desc'),
                  'element': skill.get('element'), 'power': skill.get('mag'),
                  'damageType': skill.get('dmgType'), 'target': skill.get('target'), 'hits': skill.get('hits')}
        if mapping:
            try:
                bundle = native.target_effects(sid)
                motion = 'attack' if skill.get('dmgType') == 'Physic' else 'cast/release'
                record.update(mapping, status='audited_target_effects',
                              presentation=f"Recipient {motion}; {mapping['donorName']} target effect; return to idle.",
                              requiredWork='Applied automatically when selected; preserve mechanics and native sequences. Needs representative in-game verification.',
                              particleEvents=sum(e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget' for e in bundle['events']))
            except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError, subprocess.SubprocessError) as error:
                record.update(mapping, status='effect_error', reason=str(error))
        elif skill.get('seq'):
            record.update(status='native_sequence_retained', presentation='Existing FFR timeline retained; caster portability is not proven by this audit.')
        elif sid in (400260, 400300):
            record.update(status='existing_authored_trial', presentation='Retain tested Steal/Barrage presentation.')
        elif skill.get('attr') in ('Ability', 'Magic', 'MagicSword', 'Fight') and 0 < int(skill.get('hits') or 0) <= 30:
            record.update(status='motion_only_fallback', presentation='Recipient attack/cast and original resolutions; no invented effect. Needs a specific visual rule.')
        else:
            record.update(status='specialized_or_internal', presentation='Inspect specialized runtime routing; ordinary attack profiles do not establish correct behavior.')
        records.append(record)
    return {'schema': 1, 'inGameValidated': False,
            'scope': 'Full raw catalog, including hidden/internal entries. Studio hiding and duplicate rules are unchanged.',
            'summary': dict(collections.Counter(r['status'] for r in records)), 'skills': records}


def write_report(report, prefix):
    prefix = Path(prefix); prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fields = ['id', 'name', 'description', 'element', 'power', 'damageType', 'target', 'hits',
              'status', 'donor', 'donorName', 'rule', 'tier', 'particleEvents', 'presentation', 'requiredWork', 'reason']
    with prefix.with_suffix('.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(report['skills'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--rows', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--decoder', type=Path)
    parser.add_argument('--dotnet', type=Path)
    parser.add_argument('--usmap', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    root = args.engine.resolve()
    catalog = args.catalog or next(p for p in (root/'build/devui/ffr_catalog.json', root/'data/ffr_catalog.json') if p.is_file())
    rows_root = args.rows or root/'extracted/rows'
    def rows(relative):
        path = rows_root / (relative + '.json')
        if not path.exists(): path = rows_root / (Path(relative).name + '.json')
        return json.loads(path.read_text(encoding='utf-8-sig'))['rows'] if path.exists() else {}
    decoder = args.decoder or root/'bin/ffr-dt.exe'
    command = ([str(args.dotnet)] if args.dotnet else []) + [str(decoder)]
    cache = DecoderCache(command, args.usmap or root/'extracted/Mappings.usmap', root/'build/animation-audit-cache')
    path = Path(__file__).resolve().parent.parent/'assets/existing_visions/payload/_ffr_animation_repair.py'
    spec = importlib.util.spec_from_file_location('animation_audit_payload', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    def missing(folder): raise FileNotFoundError('Missing prepared native folder: ' + folder)
    native = module.NativeAnimations(rows, root, missing,
        {'dumps': cache.dumps, 'keys': lambda p: scheduled_keys(*cache.dumps(p))})
    native.catalog = json.loads(catalog.read_text(encoding='utf-8-sig'))
    native.visual_policy = module.effect_policy(native.catalog, native.skills, native.effects)['skills']
    report = audit_catalog(native); write_report(report, args.report)
    print(json.dumps(report['summary'], indent=2))
    return int(bool(report['summary'].get('effect_error')))


if __name__ == '__main__': raise SystemExit(main())
