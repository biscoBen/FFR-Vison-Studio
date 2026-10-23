"""Revision 6: five MR passives per vision, preserving all 131 excluded bonuses.

The order is MR 1/3/5/7/9. Active grants keep their recipes and return to
awakening. No passive effects are combined and original game rows stay intact.
"""
import copy
import json
from pathlib import Path

from sephira_reward_sources import LABELS

REWARDS = {
    'a2': [1309, 1421, 1422, 1423, 1424],
    'christine': [1281, 1376, 1407, 1406, 1045],
    'crystal_fina': [1283, 1551, 1077, 1552, 1042],
    'barusa': [1526, 1336, 1452, 1453, 1454],
    'fran': [1125, 1128, 1126, 1321, 1337],
    'lunafreya': [1131, 1286, 1275, 1425, 1468],
    'minfilia': [1465, 1343, 1410, 1411, 1412],
    'folka': [1380, 1307, 1524, 1348, 1367],
    'fryevia': [1463, 1539, 1415, 1416, 1414],
    'lenneth': [1290, 1029, 1331, 1408, 1409],
    'lila': [1379, 1284, 1288, 1325, 1353],
    'mystea': [1313, 1315, 1299, 1530, 1030],
    'reberta': [1507, 1257, 1320, 1335, 1442],
    'snow_white': [1318, 1358, 1405, 1431, 1457],
    'aria': [1104, 1251, 1381, 1311, 1527],
    'eiko': [1009, 1107, 1338, 1498, 1031],
    'alice': [1106, 1247, 1234, 1294, 1388],
    'mog': [1316, 1287, 1277, 1511, 1049],
    'lilith': [1513, 1369, 1339, 1333, 1413],
    'freya': [1116, 1362, 1361, 1466, 1357],
    'trance_terra': [1038, 1319, 1432, 1351, 1433],
    'ariana': [1105, 1114, 1293, 1499, 1050],
    'elephim': [1250, 1285, 1235, 1292, 1386],
    'jade': [1323, 1366, 1385, 1371, 1359],
    'primm': [1011, 1378, 1273, 1531, 1460],
    'relm': [1066, 1237, 1279, 1360, 1280],
    'rikku': [1056, 1387, 1426, 1435, 1436],
    'nalu': [1124, 1523, 1399, 1420, 1418],
    'elza': [1253, 1317, 1528, 1434, 1428],
    'lunera': [1248, 1258, 1510, 1458, 1051],
}


def revise(catalog, audit, rows, english):
    passive = {r['ID']: r for r in rows('Skill/DT_PassiveSkillData').values()}
    names = {r['id']: r['name'] for r in english['passives']}
    mandatory = {e['id'] for e in audit['entries'] if e['kind'] == 'PassiveSkill'}
    selected = [sid for ids in REWARDS.values() for sid in ids]
    if len(selected) != len(set(selected)) or len(selected) != 150 or not mandatory <= set(selected):
        raise ValueError('MR curation must preserve all 131 distinct original passives, once each.')
    protected = {r['source'] for r in catalog['protectedMrRewards'] if r['kind'] == 'PassiveSkill'}
    if set(selected) & protected: raise ValueError('Curation uses a kept original MR reward.')
    for preset in catalog['presets']:
        unit = preset['profile']; key = preset['id']; choices = REWARDS[key]
        if unit.get('sephiraRecipe', 0) >= 6: continue
        preset['revision5Progression'] = {field: copy.deepcopy(unit.get(field, {}))
                                        for field in ('awakening', 'synchro', 'sephiraPassiveText')}
        before = [g for field in ('awakening', 'synchro') for tier in unit[field]
                  for g in tier if g[0] == 'PassiveSkill']
        active_mr = [(rank, copy.deepcopy(g)) for rank, tier in enumerate(unit['synchro'])
                     for g in tier if g[0] == 'ActiveSkill']
        unit['awakening'] = [[g for g in tier if g[0] != 'PassiveSkill'] for tier in unit['awakening']]
        for rank, grant in active_mr:
            # The first two MR abilities remain available at initial awakening;
            # later ones unlock with the corresponding progression tier.
            preferred = min(3, max(0, (rank - 3) // 2))
            target = next((r for r in [preferred, *range(preferred + 1, 4), *range(preferred)]
                           if len(unit['awakening'][r]) < 8), None)
            if target is None: raise ValueError(f'{key}: active awakening grants exceed native capacity')
            unit['awakening'][target].append(grant)
        unit['synchro'] = [[g for g in tier if g[0] not in ('ActiveSkill', 'PassiveSkill')]
                           for tier in unit['synchro']]
        for rank, identity in zip((1, 3, 5, 7, 9), choices):
            if identity not in passive: raise ValueError(f'Missing native passive {identity}')
            unit['synchro'][rank].insert(0, ['PassiveSkill', identity, -1])
        unit['sephiraPassiveText'] = {str(sid): dict(zip(('name', 'desc'), LABELS[sid]))
                                    for sid in choices if sid in LABELS}
        unit['sephiraRecipe'] = 6
        preset['masteryCuration'] = {'removedPassives': [g[1] for g in before if g[1] not in choices],
                                    'originalPassives': [sid for sid in choices if sid in mandatory],
                                    'extraPassives': [sid for sid in choices if sid not in mandatory]}
        balance = preset['balance']
        balance.update(activeCount=sum(len(t) for t in unit['awakening']), passiveCount=0,
                       kitCount=sum(len(t) for t in unit['awakening']), mrActiveCount=0,
                       mrPassiveCount=5, mrSkillCount=5,
                       totalSkillCount=sum(len(t) for t in unit['awakening']) + 5,
                       additionalPassives=[sid for sid in choices if sid not in mandatory])
        for recipe in balance['playerCopies']:
            recipe['unlock'] = next([field, rank] for field in ('awakening', 'synchro')
                                   for rank, tier in enumerate(unit[field])
                                   if any(g[0] == 'ActiveSkill' and g[1] == recipe['id'] for g in tier))
    owner = {sid: key for key, ids in REWARDS.items() for sid in ids}
    for entry in audit['entries']:
        if entry['kind'] == 'PassiveSkill': entry['assignedTo'] = owner[entry['id']]
    audit['status'] = 'All 160 active skills and 131 original passives allocated once; every passive is an odd-rank MR reward.'
    catalog['passiveCuration'] = {'revision': 6, 'originalCount': len(mandatory),
                                 'extraCount': len(set(selected) - mandatory), 'totalCount': len(selected)}
    lines = ['# Sephira passive mastery allocation', '',
             'Revision 6 preserves every one of the 131 distinct passives from the 15 excluded original visions, once each. '
             'The other 19 slots retain distinctive equipment bonuses and Knight of the Sacred Frost. '
             'Each vision has exactly one passive at MR 1, 3, 5, 7 and 9. Active MR skills return to awakening; '
             'all active recipes, permanent stat budgets and Spirit rewards are retained. '
             'Passives are native individual effects, without combined effects or extra grants at a rank.', '',
             'Some passives move between visions to make room for the complete original collection. '
             'Lenneth keeps Physical Counter with Lustrous Shield; Fryevia keeps her spellblade trio and gains Knight of the Sacred Frost. '
             'Redundant permanent imbues are omitted where the kit already earns the same elemental imbue through attacks.', '',
             '| Vision | MR 1 | MR 3 | MR 5 | MR 7 | MR 9 |', '|---|---|---|---|---|---|']
    for preset in catalog['presets']:
        values = []
        for sid in REWARDS[preset['id']]:
            name = LABELS[sid][0] if sid in LABELS else names[sid]
            values.append(f'{name} ({sid})' + (' †' if sid not in mandatory else ''))
        lines.append('| ' + ' | '.join([preset['name'], *values]) + ' |')
    lines += ['', '† One of the 19 additional bonuses. Original provenance and exact mechanics remain in '
              '`assets/sephira_visions/native_coverage.json`.', '',
              'Use **Apply MR and acquisition update** once for saved collection entries, then rebuild/install. '
              'The backed-up migration replaces the passive selection, preserves active skill edits and learned active grants, '
              'and keeps existing permanent rewards, artwork, IDs and acquisition settings. '
              'New and restored presets already include this allocation. Later edits remain yours.', '']
    Path(__file__).resolve().parents[1].joinpath('docs/SEPHIRA_PASSIVE_MASTERY.md').write_text('\n'.join(lines))
