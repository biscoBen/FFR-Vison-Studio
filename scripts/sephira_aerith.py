"""Replace Elephim's presentation with original 5-star Aerith, retaining save IDs."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FORM = '207000405'
PACK_SHA256 = '33548cfcae22899581dfa57341d8074f5c67b989618fe69e3009e825573d2495'


def revise(catalog):
    preset = next(p for p in catalog['presets'] if p['id'] == 'elephim')
    unit = preset['profile']
    if unit.get('sephiraAppearanceRevision', 0) >= 1: return catalog
    # The internal preset/key, vision ID, command ID and Spirit ID are permanent.
    before = copy.deepcopy(unit)
    preset['name'] = unit['en'] = 'Aerith'
    preset['theme'] = 'Support and debuff magic with Great Gospel healing'
    unit['desc'] = preset['theme'] + '.'
    unit['command'].update(en='Aerith Skills', desc='Support and debuff magic.')
    unit['master'].update(en='Spirit of Aerith', desc="Aerith's learned mastery rewards flow into the wearer.")
    unit['ffbe'] = {'id': FORM, 'base': FORM, 'source': 'GL',
                    'dir': 'units/ffbe/sephira_elephim/sprites/' + FORM}
    unit['lb'] = 412510  # Native Ayaka: group healing, debuff removal and Esuna.
    lb = unit['lb_custom']
    lb.update({'from': unit['lb'], 'ffbe_lb_id': FORM, 'en': 'Great Gospel',
               'desc': 'Restore HP, remove debuffs, and cure all status ailments other than KO for all allies.'})
    preset.get('descriptionUpdate', {}).pop('resonance', None)
    preset['form'] = {'id': FORM, 'label': '5', 'sha256': PACK_SHA256, 'source': 'GL'}
    unit['sephiraAppearanceRevision'] = 1
    preset['appearanceUpdate'] = {'schema': 1, 'version': 1, 'from': before['ffbe']['id'],
        'fields': {k: copy.deepcopy(unit[k]) for k in ('en','desc','ffbe','lb','lb_custom')},
        'command': {k: unit['command'][k] for k in ('en','desc')},
        'master': {k: unit['master'][k] for k in ('en','desc')}}
    return catalog


def update_audio(source, tools, archive):
    """Add Aerith's two clean source recordings without rebuilding other audio."""
    sys.path.insert(0, str(tools))
    from ffbe_effects.acb_cues import cues, utf
    from ffbe_effects import acb_native, hca_host
    with zipfile.ZipFile(archive) as bundle:
        files = {name: bundle.read(name) for name in bundle.namelist()}
    metadata = json.loads(files.pop('manifest.json'))
    bank = source / 'memorial-source/SE.acb'; raw = bank.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == metadata['sourceBanks']['SE']
    cue_index = cues(bank); ids = {793, 794}
    recordings = acb_native.recordings(raw, ids, {cid: cue_index[cid]['name'] for cid in ids})
    waves = acb_native.awb_files(utf(raw)[1][0]['AwbFile'])
    doc = json.loads(files['audio/SE.json'])
    doc['recordings'] = [r for r in doc['recordings'] if r['sourceCueId'] not in ids] + recordings
    for cid in sorted(ids):
        entry = cue_index[cid]
        doc['cues'][str(cid)] = {'name': entry['name'], 'cueIndex': entry['cueIndex'],
            'durationMs': max(r['durationMs'] for r in recordings if r['sourceCueId'] == cid)}
    for recording in recordings:
        wid = str(recording['sourceWaveId']); sample = waves[int(wid)]
        hca_host.validate_layout(sample)
        digest = hashlib.sha256(sample).hexdigest()
        if wid in doc['waves']: assert doc['waves'][wid]['sha256'] == digest
        doc['waves'][wid] = {'sha256': digest}
        files['audio/samples/' + digest + '.hca'] = sample
    files['audio/SE.json'] = json.dumps(doc, separators=(',', ':')).encode()
    lbs = {r['PR2HIc71']: r for r in json.loads((source/'F_LIMITBURST_MST-memorial.json').read_bytes())}
    groups = {r['qIy86WvJ']: r for r in json.loads((source/'F_EFFECT_GROUP_MST-memorial.json').read_bytes())}
    timeline = lbs[FORM]['5A8SmwyC'].split('@')[0].split('&'); sounds = []
    for event in timeline:
        offset, gid, *_ = event.split(':')
        for sound in filter(None, groups[gid].get('1fVZ3rKd', '').split(',')):
            frame, cue, *flags = sound.split(':')
            assert int(cue) in ids and flags == ['1']
            sounds.append({'frame': int(offset)+int(frame), 'cueId': int(cue), 'groupId': gid,
                           'groupFrame': int(offset), 'cueFrame': int(frame), 'flags': flags})
    metadata['profiles']['elephim'] = {'form': FORM, 'lbId': FORM, 'name': 'Aerith',
        'sourceName': lbs[FORM]['G4L0YIB2'], 'variant': 0, 'timeline': timeline,
        'sounds': sorted(sounds, key=lambda s: s['frame']), 'adaptation': None,
        'status': 'original_cues', 'reason': None}
    metadata['files'] = {k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items())}
    files['manifest.json'] = json.dumps(metadata, indent=2, ensure_ascii=False).encode()
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 27, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data)


if __name__ == '__main__':
    path = ROOT/'assets/sephira_visions/catalog.json'
    catalog = revise(json.loads(path.read_bytes()))
    path.write_text(json.dumps(catalog, indent=2)+'\n')
    policy = ROOT/'assets/existing_visions/payload/sephira_visuals.json'
    data = json.loads(policy.read_bytes())
    data['appearanceUpdates'] = {p['id']: p['appearanceUpdate'] for p in catalog['presets'] if p.get('appearanceUpdate')}
    policy.write_text(json.dumps(data, indent=2)+'\n')
