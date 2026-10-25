"""Restore the awakening bonus layer without disturbing revision 6's MR collection.

Budgets use each preset's original stat/Resonance counterpart's COMPLETE passive
kit (awakening plus MR), rather than adding the same number to every vision.
Native effects and equip costs stay intact; these are choices, not free stats.
"""
import copy
import json
from pathlib import Path

from sephira_reward_sources import LABELS

# In approximate unlock order. Avoid another tier of the same percentage bonus
# on one vision, and prefer native utility that fits the selected FFBE identity.
BONUSES = {
    'a2': [1378, 1105, 1124, 1247, 1376],
    'christine': [1380, 1033, 1277, 1285, 1280],
    'crystal_fina': [1381, 1107, 1277, 1455, 1456],
    'barusa': [1313, 1106, 1290, 1379, 1331, 1333],
    'fran': [1309, 1277, 1338, 1376],
    'lunafreya': [1380, 1107, 1251, 1315, 1336, 1281, 1277],
    'minfilia': [1311, 1116, 1381, 1277, 1313, 1336],
    'folka': [1275, 1107, 1281, 1293, 1315],
    'fryevia': [1309, 1033, 1277, 1378],
    'lenneth': [1313, 1378, 1299, 1235, 1253, 1042],
    'lila': [1309, 1247, 1277, 1331],
    'mystea': [1379, 1253, 1042, 1338, 1336],
    'reberta': [1309, 1011, 1378, 1286, 1293, 1247, 1376],
    'snow_white': [1309, 1253, 1378, 1313, 1077],
    'aria': [1375, 1111, 1300, 1301, 1352],
    'eiko': [1375, 1106, 1381, 1277, 1455],
    'alice': [1309, 1105, 1378, 1124, 1376],
    'mog': [1311, 1251, 1378, 1286, 1320],
    'lilith': [1313, 1252, 1378, 1331, 1042],
    'freya': [1309, 1311, 1247, 1277, 1279, 1378, 1335, 1320, 1360],
    'trance_terra': [1275, 1107, 1381, 1315, 1307],
    'ariana': [1375, 1107, 1381, 1277, 1455],
    'elephim': [1311, 1107, 1381, 1336, 1277],
    'jade': [1309, 1250, 1247, 1378, 1277, 1234],
    'primm': [1311, 1116, 1381, 1277, 1293, 1284],
    'relm': [1275, 1107, 1381, 1315, 1307],
    'rikku': [1317, 1114, 1378, 1287, 1124],
    'nalu': [1309, 1250, 1247, 1378, 1279, 1234],
    'elza': [1309, 1251, 1378, 1124, 1320],
    'lunera': [1309, 1277, 1281, 1376],
}


def revise(catalog, rows, english):
    passive = {r['ID']: r for r in rows('Skill/DT_PassiveSkillData').values()}
    names = {r['id']: r['name'] for r in english['passives']}
    protected = {r['source'] for r in catalog['protectedMrRewards'] if r['kind'] == 'PassiveSkill'}
    awakening = list(rows('Item/Vision/DT_VisionAwakeningMasteryData').values())
    mastery = list(rows('Item/Vision/DT_VisionSynchroMasteryData').values())
    for preset in catalog['presets']:
        unit = preset['profile']; key = preset['id']
        if unit.get('sephiraRecipe', 0) >= 7: continue
        if unit.get('sephiraRecipe') != 6: raise ValueError('Apply passive mastery revision 6 first.')
        before = copy.deepcopy(unit)
        budget = preset['balance']['nativeBudget']
        native = [g['params'][0] for t in awakening + mastery if t['ID'] == budget
                  for g in t['detailData'] if g['parameterType'] == 'PassiveSkill']
        ids = BONUSES[key]
        owned = {g[1] for tier in unit['synchro'] for g in tier if g[0] == 'PassiveSkill'}
        if len(ids) + len(owned) != len(native) or len(set(ids)) != len(ids) or owned & set(ids):
            raise ValueError(key + ': duplicate bonuses or wrong complete-kit budget')
        if set(ids) & protected: raise ValueError(key + ': kept original MR reward')
        # Four awakening tiers; stronger options generally come later. When a
        # saved tier is full, spill later rather than moving active skills.
        grants = []
        for index, identity in enumerate(ids):
            preferred = min(3, index * 4 // len(ids))
            rank = next((r for r in range(preferred, 4) if len(unit['awakening'][r]) < 8), None)
            if rank is None: raise ValueError(key + ': no awakening room for bonuses')
            unit['awakening'][rank].append(['PassiveSkill', identity, -1])
            grants.append({'rank': rank, 'id': identity})
        current = [*owned, *ids]
        cost = lambda choices: sum(passive[s]['equipCost'] or 20 for s in choices)
        ratio = cost(current) / cost(native)
        if not .8 <= ratio <= 1.2: raise ValueError(key + ': passive equip-cost budget outside native range')
        preset['awakeningBalance'] = {
            'revision': 7, 'nativeBudget': budget, 'nativeName': preset['balance']['nativeName'],
            'nativePassiveCount': len(native), 'totalPassiveCount': len(current),
            'nativeEquipCost': cost(native), 'equipCost': cost(current), 'grants': grants,
            'nativePassives': native,
        }
        unit['sephiraPassiveText'].update({str(s): dict(zip(('name','desc'), LABELS[s]))
                                          for s in ids if s in LABELS})
        unit['sephiraRecipe'] = 7
        balance = preset['balance']
        balance.update(passiveCount=len(ids), kitCount=balance['activeCount'] + len(ids),
                       totalSkillCount=balance['activeCount'] + len(ids) + 5)
        if any(before[f] != unit[f] for f in before if f not in ('awakening','sephiraRecipe','sephiraPassiveText')):
            raise ValueError(key + ': bonus update changed another part of the kit')
    write_report(catalog, names)


def write_report(catalog, names):
    lines = ['# Sephira awakening bonus balance', '',
        'The current layout retains all 75 excluded-original equipable MR rewards as MR rewards, '
        'all 131 distinct excluded-original passives across the complete kits, permanent stats and acquisition settings. '
        'Each complete kit has the same number of passives as its native stat/Resonance counterpart. '
        'This is a per-vision comparison: paired challenge rewards do not divide one original kit between two visions.', '',
        'Choices follow each unit’s role. Native effects and AP equip costs are unchanged, so these are learned '
        'options rather than free permanent bonuses. Combined passive equip-cost totals stay within 20% of the '
        'counterpart; this is a useful budget check, not a claim that AP costs measure combat strength exactly. '
        'No second percentage tier of the same main stat is added to a kit. The existing active skill, stat and '
        'Resonance budgets remain; playing the game is still needed to assess difficult combinations.', '',
        'The earlier rule reserving passives for MR is extended here at the user’s request: supplementary passives '
        'are awakening bonuses and stay out of battle commands. MR still has one reward per rank, with three at MR 9. '
        'Kept original visions’ MR rewards are still excluded.', '',
        '| Vision | Native counterpart | Total passives | Awakening bonuses | Passive AP total (original) |',
        '|---|---|---:|---|---:|']
    for p in catalog['presets']:
        b = p['awakeningBalance']
        display = lambda sid: LABELS[sid][0] if sid in LABELS else names[sid]
        bonuses = '; '.join(f"A{g['rank']+1}: {display(g['id'])}" for g in b['grants'])
        lines.append(f"| {p['name']} | {b['nativeName']} | {b['totalPassiveCount']} | {bonuses} | {b['equipCost']} ({b['nativeEquipCost']}) |")
    lines += ['', 'For saved collection entries, use **Apply MR and acquisition update**, then rebuild/install. '
        'Unedited saved reward layouts migrate automatically with a roster backup. The MR restoration replaces '
        '25 supplemental MR passives with the original active rewards and moves supplemental passives into awakening. '
        'Deliberate edits to affected MR slots and full awakening kits report conflicts before saving. '
        'Artwork, identities, private combat recipes, permanent rewards and locations are retained. '
        'New/restored presets include the current layout. See [the MR restoration](SEPHIRA_MR_RESTORATION.md).', '']
    Path(__file__).resolve().parents[1].joinpath('docs/SEPHIRA_AWAKENING_BALANCE.md').write_text('\n'.join(lines),encoding='utf-8')
