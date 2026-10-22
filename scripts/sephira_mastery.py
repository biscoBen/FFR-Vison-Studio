"""Role-based MR schedules using the native five-ability/five-stat structure.

Keep every learned ability once. Surplus MR abilities move to awakening 4;
powerful defining abilities finish the MR track rather than sharing a rank.
"""
import copy

# MR1, 3, 5, 7, 9. IDs refer to the authored profile, before identity remapping.
ABILITIES = {
    'a2': [1421, 1278, 1422, 1478, 400710],
    'christine': [1281, 1255, 400630, 1406, 1045],
    'crystal_fina': [1252, 1393, 400740, 1397, 1456],
    'barusa': [1336, 400640, 1118, 1454, 1453],
    'fran': [400450, 1127, 1337, 1443, 1444],
    'lunafreya': [1326, 1298, 1396, 1468, 1425],
    'minfilia': [400240, 1099, 1465, 1343, 1410],
    'folka': [1254, 400680, 1307, 1445, 400360],
    'fryevia': [1344, 1071, 400350, 1415, 1414],
    'lenneth': [1331, 400390, 1029, 1409, 1042],
    'lila': [1284, 1322, 400440, 1048, 400650],
    'mystea': [1314, 1395, 1303, 486106, 1402],
    'reberta': [1320, 400210, 1257, 1335, 1437],
    'snow_white': [1318, 400490, 1302, 1358, 1405],
    'aria': [1282, 1356, 400550, 1256, 1305],
    'eiko': [1479, 1338, 1000, 1047, 1031],
    'alice': [1324, 400530, 1330, 1388, 1234],
    'mog': [1316, 400760, 1004, 1049, 230140],
    'lilith': [1036, 400380, 1333, 1339, 1259],
    'freya': [1394, 400280, 1349, 1438, 1340],
    'trance_terra': [1319, 1038, 1351, 1065, 400730],
    'ariana': [1476, 400460, 1392, 400540, 1464],
    'elephim': [1295, 1235, 1304, 1074, 487318],
    'jade': [1323, 1371, 400310, 1385, 400700],
    'primm': [1310, 1329, 400660, 1370, 400770],
    'relm': [1328, 1280, 400720, 1332, 400330],
    'rikku': [400260, 1044, 400270, 1050, 400750],
    'nalu': [1124, 1399, 1400, 1404, 1418],
    'elza': [1383, 1389, 1403, 1398, 1428],
    'lunera': [1066, 1258, 1345, 1341, 1449],
}

# Three distinct relevant parameters at MR2/6/8. Each uses the native
# 5/10/15-point budget; HP converts at 6:1 and MP at 2:1, as native rewards do.
STATS = {
    'a2': [1, 9, 5], 'christine': [9, 2, 7], 'crystal_fina': [1, 2, 8],
    'barusa': [1, 6, 5], 'fran': [9, 1, 5], 'lunafreya': [9, 2, 7],
    'minfilia': [5, 2, 7], 'folka': [8, 2, 7], 'fryevia': [9, 1, 5],
    'lenneth': [8, 1, 6], 'lila': [1, 9, 5], 'mystea': [1, 6, 8],
    'reberta': [1, 9, 5], 'snow_white': [1, 6, 5], 'aria': [2, 7, 8],
    'eiko': [8, 2, 7], 'alice': [1, 9, 5], 'mog': [7, 2, 9],
    'lilith': [1, 8, 6], 'freya': [1, 9, 5], 'trance_terra': [9, 2, 7],
    'ariana': [7, 2, 8], 'elephim': [8, 2, 9], 'jade': [1, 9, 5],
    'primm': [5, 2, 7], 'relm': [9, 2, 7], 'rikku': [1, 5, 9],
    'nalu': [9, 1, 5], 'elza': [1, 9, 5], 'lunera': [9, 1, 5],
}


def schedule(key, unit):
    """Reorganize an authored preset in place; never operate on a saved roster."""
    wanted = ABILITIES[key]
    grants = {}
    for field in ('awakening', 'synchro'):
        for tier in unit[field]:
            for grant in tier:
                if grant[0] in ('ActiveSkill', 'PassiveSkill'):
                    identity = grant[1]
                    if identity in grants:
                        raise ValueError(f'{key}: duplicate ability {identity}')
                    grants[identity] = copy.deepcopy(grant)
    if not set(wanted) <= grants.keys():
        raise ValueError(f'{key}: missing MR selections {set(wanted) - grants.keys()}')
    awakening = [[copy.deepcopy(g) for g in tier if g[1] not in wanted]
                 for tier in unit['awakening']]
    retained = {g[1] for tier in awakening for g in tier}
    # Newly awakened former MR rewards stay late in progression. Fill the final
    # tier first, then the third, preserving native eight-slot struct limits.
    for identity, grant in grants.items():
        if identity in wanted or identity in retained:
            continue
        tier = next((awakening[r] for r in (3, 2, 1, 0) if len(awakening[r]) < 8), None)
        if tier is None:
            raise ValueError(f'{key}: no awakening room for displaced MR reward')
        tier.append(grant)
    mastery = [[] for _ in range(10)]
    for rank, identity in zip((1, 3, 5, 7, 9), wanted):
        mastery[rank].append(grants[identity])
    for rank, parameter, points in zip((2, 6, 8), STATS[key], (5, 10, 15)):
        mastery[rank].append(['BaseParameter', parameter, points * {1: 6, 2: 2}.get(parameter, 1)])
    mastery[4].append(['BaseParameter', 11, 8])
    mastery[9].extend([['BaseParameter', 11, 8], ['MasterSkill', unit['master']['id'], -1]])
    unit.update(awakening=awakening, synchro=mastery, sephiraRecipe=4)
