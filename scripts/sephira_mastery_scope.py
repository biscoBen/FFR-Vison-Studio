"""Keep unit-bound traits in awakening; retain transferable MR rewards."""
import copy
import importlib.util
from pathlib import Path
import re


def runtime_rules():
    path = Path(__file__).resolve().parents[1]/'assets/existing_visions/payload/_ffr_sephira.py'
    spec = importlib.util.spec_from_file_location('_mastery_scope_rules', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def rules(): return runtime_rules().MASTERY_SCOPE


def revise(catalog, english=None):
    for preset in catalog['presets']:
        route = runtime_rules().ACQUISITION_SWAPS.get(preset['id'])
        if route: preset['acquisitionUpdate'] = {'schema':1,'before':route[0],'after':route[1]}
        swaps = rules().get(preset['id'], [])
        if not swaps or preset.get('masteryScopeUpdate'): continue
        unit = preset['profile']
        preset['masteryScopeUpdate'] = {'schema': 1, 'swaps': swaps,
            'before': {f: copy.deepcopy(unit[f]) for f in ('awakening', 'synchro')}}
        for rank, bound, general, preferred in swaps:
            reward = next(g for g in unit['synchro'][rank] if g[:2] == ['PassiveSkill', bound])
            bonus = next(g for tier in unit['awakening'] for g in tier if g[:2] == ['PassiveSkill', general])
            reward[1], bonus[1] = general, bound
            next(g for g in preset['awakeningBalance']['grants'] if g['id'] == general)['id'] = bound
        unit['sephiraPassiveText'].update({str(sid):dict(zip(('name','desc'),text))
            for sid,text in runtime_rules().MASTERY_LABELS[preset['id']].items()})
    write_reports(catalog, english)


def write_reports(catalog, english=None):
    root=Path(__file__).resolve().parents[1]
    mastery=root/'docs/SEPHIRA_PASSIVE_MASTERY.md'
    if not mastery.is_file():return
    text=mastery.read_text()
    names={int(sid):name.strip() for name,sid in re.findall(r'([^|\n]+?) \((\d+)\)',text)}
    if english: names.update({r['id']:r['name'] for r in english['passives']})
    for labels in runtime_rules().MASTERY_LABELS.values():
        names.update({sid:v[0] for sid,v in labels.items()})
    for preset in catalog['presets']:
        if not preset.get('masteryScopeUpdate'):continue
        row='| '+preset['name']+' | '+' | '.join(
            names[preset['profile']['synchro'][r][0][1]]+' ('+str(preset['profile']['synchro'][r][0][1])+')'
            for r in (1,3,5,7,9))+' |'
        text=re.sub(r'^\| '+re.escape(preset['name'])+r' \|.*$',lambda m:row,text,flags=re.M)
    text=text.replace('This table remains the current MR allocation. [Revision 7](SEPHIRA_AWAKENING_BALANCE.md) adds a separate awakening bonus layer without removing these rewards.',
        'This is the current MR allocation. The scope correction swaps eight command/LB-bound traits with existing general awakening bonuses, without adding or removing a passive or changing AP budgets. Christine’s True Stagger is an awakening bonus; MR7 grants Fill LB on Stagger. The same rule applies to Barusa, Minfilia, Trance Terra and Nalu.')
    text=text.replace('Revision 6 preserves every one of the 131 distinct passives from the 15 excluded original visions, once each.',
        'All 131 distinct passives from the 15 excluded original visions remain in the complete kits. Command/LB-bound traits stay with their vision; MR rewards transfer between visions.')
    mastery.write_text(text)
    if not english:return
    awakening=root/'docs/SEPHIRA_AWAKENING_BALANCE.md'
    text=awakening.read_text()
    for preset in catalog['presets']:
        if not preset.get('masteryScopeUpdate'):continue
        b=preset['awakeningBalance']
        bonuses='; '.join('A'+str(g['rank']+1)+': '+names[g['id']] for g in b['grants'])
        row=f"| {preset['name']} | {b['nativeName']} | {b['totalPassiveCount']} | {bonuses} | {b['equipCost']} ({b['nativeEquipCost']}) |"
        text=re.sub(r'^\| '+re.escape(preset['name'])+r' \|.*$',lambda m:row,text,flags=re.M)
    text=text.replace('while preserving every revision 6 MR reward,',
        'while preserving the complete passive collection. The scope correction relocates eight unit-bound MR traits into existing awakening bonus slots; their general bonuses move to MR. It preserves')
    awakening.write_text(text)

