"""Requested first-playthrough acquisition groups (not stat-budget donors)."""
GROUPS = {
    13024: ['christine'],
    13062: ['barusa', 'ariana'],
    13100: ['lenneth', 'crystal_fina'],
    13101: ['lila', 'fran'],
    13102: ['minfilia', 'primm'],
    13103: ['snow_white', 'lilith', 'mystea'],
    13105: ['fryevia', 'lunera'],
    13110: ['nalu', 'jade'],
    13116: ['a2', 'alice'],
    13118: ['rikku', 'eiko'],
    13120: ['elza', 'mog'],
    13123: ['trance_terra', 'relm'],
    13124: ['lunafreya', 'elephim'],
    13128: ['freya'],
    13130: ['reberta'],
}


def acquisition(key):
    if key == 'aria':
        return {'version': 1, 'location': 'mitra_shop', 'random': False, 'hideSpoilers': True}
    origin = next((native for native, keys in GROUPS.items() if key in keys), None)
    location = 'sephira_folka_shop' if key == 'folka' else 'sephira_' + str(origin)
    if origin is None and key != 'folka': raise ValueError('Unassigned Sephira acquisition: ' + key)
    return {'version': 3, 'location': location, 'random': False, 'hideSpoilers': True, 'cave': None}
