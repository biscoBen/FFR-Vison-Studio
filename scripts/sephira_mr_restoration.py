"""Restore all native MR equipables at their original gates and mastery ranks.

The reviewed allocation retains each vision's native passive count and AP
budget, all original passives, the authored healer kits and existing mechanics.
"""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'scripts/fixtures/sephira_mr_restoration_plan.json'


def revise(catalog,coverage,rows):
    plan=json.loads(PLAN.read_bytes())
    if all(p['profile'].get('sephiraMrRevision')==1 for p in catalog['presets'] if p['id'] in plan['awakening']):return catalog
    before={p['id']:copy.deepcopy(p) for p in catalog['presets']}
    by={p['id']:p for p in catalog['presets']}
    active={sid for _,_,sid in plan['placements']}
    destinations={sid:key for key,_,sid in plan['placements']}
    for key,rank,sid in plan['placements']:by[key]['profile']['synchro'][rank][0]=['ActiveSkill',sid,-1]
    for key,rank,sid in plan['relocations']:by[key]['profile']['synchro'][rank][0]=['PassiveSkill',sid,-1]
    for preset in catalog['presets']:
        unit=preset['profile'];key=preset['id']
        if key not in plan['awakening']:continue
        unit['awakening']=[[g for g in tier if not (g[0]=='PassiveSkill' or (g[0]=='ActiveSkill' and destinations.get(g[1])==key))]
                           for tier in unit['awakening']]
        for bonus in plan['awakening'][key]:unit['awakening'][bonus['rank']].append(['PassiveSkill',bonus['id'],-1])
        old=before[key]['profile']
        changes=[{'rank':r,'from':old['synchro'][r][0],'to':unit['synchro'][r][0]}
                 for r in (1,3,5,7,9) if old['synchro'][r][0]!=unit['synchro'][r][0]]
        def index(value):return {(g[0],g[1]):r for r,t in enumerate(value) for g in t}
        previous,current=index(old['awakening']),index(unit['awakening'])
        removed=[[r,*g] for g,r in previous.items() if current.get(g)!=r]
        added=[[r,*g] for g,r in current.items() if previous.get(g)!=r]
        assert all(g[1] in ('ActiveSkill','PassiveSkill') for g in removed+added)
        # Operations use only native IDs; private combat recipes are untouched.
        assert all(g[2] not in {int(k) for k in unit['skills']} for g in removed+added)
        preset['mrRestoration']={'version':1,'before':{f:copy.deepcopy(old[f]) for f in ('awakening','synchro')},
            'beforeAwakeningBalance':before[key]['awakeningBalance'],'mr':changes,'remove':removed,'add':added}
        unit['sephiraMrRevision']=1
        passive=[g[1] for f in ('awakening','synchro') for t in unit[f] for g in t if g[0]=='PassiveSkill']
        native={r['ID']:r for r in rows('Skill/DT_PassiveSkillData').values()}
        assert len(passive)==len(set(passive))==preset['awakeningBalance']['nativePassiveCount'],key
        cost=sum(native[s]['equipCost'] or 20 for s in passive)
        assert .8*preset['awakeningBalance']['nativeEquipCost']<=cost<=1.2*preset['awakeningBalance']['nativeEquipCost'],key
        assert all(len(t)<=8 for t in unit['awakening']),key
        preset['awakeningBalance'].update(grants=plan['awakening'][key],totalPassiveCount=len(passive),equipCost=cost)
        balance=preset['balance']
        balance.update(activeCount=sum(g[0]=='ActiveSkill' for t in unit['awakening'] for g in t),
                       passiveCount=sum(g[0]=='PassiveSkill' for t in unit['awakening'] for g in t),
                       kitCount=sum(map(len,unit['awakening'])),
                       mrActiveCount=sum(g[0]=='ActiveSkill' for t in unit['synchro'] for g in t),
                       mrPassiveCount=sum(g[0]=='PassiveSkill' for t in unit['synchro'] for g in t))
        balance['totalSkillCount']=balance['kitCount']+5
    for key in ('crystal_fina','aria'):assert by[key]['profile']==before[key]['profile']
    # Preserve native provenance and update the current canonical placements.
    def learns(p,kind,sid):
        u=p['profile']
        return any(g[:2]==[kind,sid] or (kind==g[0]=='ActiveSkill' and u['skills'].get(str(g[1]),{}).get('from')==sid)
                   for f in ('awakening','synchro') for t in u[f] for g in t)
    for entry in coverage['entries']:
        if entry['kind']=='ActiveSkill' and entry['id'] in active:
            entry['assignedTo']=next(key for key,_,sid in plan['placements'] if sid==entry['id'])
        if not learns(by[entry['assignedTo']],entry['kind'],entry['id']):
            choices=[p for p in catalog['presets'] if learns(p,entry['kind'],entry['id'])]
            assert choices,entry['id']
            origins={g['vision'] for g in entry['nativeGrants']}
            entry['assignedTo']=next((p['id'] for p in choices if p['balance']['nativeName'] in origins),choices[0]['id'])
    catalog['passiveCuration'].update(mrActiveCount=25,mrPassiveCount=125,
        distinctCount=len({g[1] for p in catalog['presets'] for t in p['profile']['synchro'] for g in t if g[0]=='PassiveSkill'}))
    coverage['status']='All 75 excluded-original MR equipables are MR rewards; all 160 original active skills and 131 passives remain learned across the complete kits.'
    runtime={'schema':1,'presets':{p['id']:{k:p['mrRestoration'][k] for k in ('version','mr','remove','add')}
                                 for p in catalog['presets'] if p.get('mrRestoration')}}
    (ROOT/'assets/existing_visions/payload/sephira_mr_restoration.json').write_text(json.dumps(runtime,indent=2)+'\n',encoding='utf-8')
    return catalog


def write_reports(catalog,coverage,english):
    """Describe the final allocation, including the equipable active rewards."""
    names={kind:{r['id']:r['name'] for r in english[key]} for kind,key in
           (('ActiveSkill','skills'),('PassiveSkill','passives'))}
    for preset in catalog['presets']:
        names['PassiveSkill'].update({int(k):v['name'] for k,v in preset['profile'].get('sephiraPassiveText',{}).items()})
    def label(g):return f"{names[g[0]][g[1]]} ({g[1]})"
    lines=['# Sephira mastery reward allocation','',
        'All 75 individual equipable MR rewards from the 15 excluded originals are available as Sephira MR rewards: '
        '50 passives and 25 active skills. Each active returns at its original MR rank and original acquisition gate. '
        'The remaining MR choices preserve themed transferable bonuses. The 150 odd-rank slots contain '
        '125 passive grants and 25 active grants, one per rank. Permanent stats, AP and Spirit rewards are unchanged.','',
        'All 131 distinct excluded-original passives remain available across the complete kits. Supplemental passives '
        'displaced from MR move into awakening, while the original MR passives stay transferable. '
        'Command/LB-bound traits remain awakening bonuses for their owners. Christine’s True Stagger stays in '
        'awakening; her transferable MR7 reward is Fill LB on Stagger.','',
        '| Vision | MR 1 | MR 3 | MR 5 | MR 7 | MR 9 |','|---|---|---|---|---|---|']
    for p in catalog['presets']:
        lines.append('| '+p['name']+' | '+' | '.join(label(p['profile']['synchro'][r][0]) for r in (1,3,5,7,9))+' |')
    lines += ['', 'The native Spirit wrapper follows its owner’s current MR rewards, including active rewards. '
        'Awakening bonuses and permanent MR stats are not copied into the Spirit. Crystal Fina and Aria retain '
        'their reviewed kits, rewards and Spirit identities unchanged. See [the healer kits](SEPHIRA_USER_KITS.md), '
        '[the MR coverage audit](SEPHIRA_MR_COVERAGE.md), and [the restoration details](SEPHIRA_MR_RESTORATION.md).','']
    (ROOT/'docs/SEPHIRA_PASSIVE_MASTERY.md').write_text('\n'.join(lines),encoding='utf-8')
    plan=json.loads(PLAN.read_bytes());by={p['id']:p for p in catalog['presets']}
    originals={e['id']:e for e in coverage['entries'] if e['kind']=='ActiveSkill'}
    lines=['# Restore the original transferable MR rewards','',
        'The complete-kit audit previously counted 25 original MR active skills as covered because they were learned '
        'in awakening. Those skills were not transferable MR rewards. The revised layout restores all 25 as MR '
        'rewards without increasing the number of rewards at any rank. All 50 original passive MR rewards remain '
        'transferable. The [reproducible coverage report](SEPHIRA_MR_COVERAGE.md) now shows 75/75.','',
        'Each restored active has its stock native mechanics, equip cost, MP cost, general-command membership and '
        'animation. Its MR rank and acquisition family match the original. Saved custom acquisition overrides '
        'remain user choices. Rikku retains the Zidane acquisition gate.','',
        '| Original vision | Reward | MR | New MR teacher |','|---|---|---:|---|']
    for key,rank,sid in plan['placements']:
        origins=', '.join(sorted({g['vision'] for g in originals[sid]['nativeGrants'] if g['track']=='synchro'}))
        lines.append(f"| {origins} | {names['ActiveSkill'][sid]} ({sid}) | {rank} | {by[key]['name']} |")
    lines += ['', '## Balance and migration','',
        'Twelve original MR passive placements move to another compatible slot, retaining their native MR rank and '
        'acquisition family. Every original MR passive stays an MR reward. All 131 excluded-original passives remain '
        'learned across the kits. Each vision keeps its native counterpart’s total passive count and stays within '
        '20% of its passive AP budget. No second percentage tier of the same main stat is added to a kit. '
        'The fixed allocation is recorded in `scripts/fixtures/sephira_mr_restoration_plan.json`; '
        '[the awakening report](SEPHIRA_AWAKENING_BALANCE.md) lists the final counts and costs.','',
        'An awakening active moves out only when that same vision now teaches it through MR. Other units retain '
        'signature awakening versions: Relm still has Mimic, for example, while Lunera teaches its MR version at '
        'Bartz’s gate. Canonical provenance identifies the MR teacher. Crystal Fina and Aria are unchanged. '
        'Private recipes, artwork, stats, permanent rewards, allocated IDs and acquisition choices are preserved.','',
        'Studio backs up and migrates untouched saved reward layouts once on loading. The build also applies the '
        'same declared migration to older configs. Deliberately edited affected MR slots or full awakening tiers '
        'are left intact and reported before building; use **Apply MR and acquisition update** after resolving '
        'the conflict. Later edits to migrated units remain user edits.','',
        'Native table writing/readback checks verify all 30 collection kits plus an independent Fina, Spirit owner '
        'bindings and all 25 stock active rows. Live-game equipment and balance still need playtesting.','']
    (ROOT/'docs/SEPHIRA_MR_RESTORATION.md').write_text('\n'.join(lines),encoding='utf-8')
    from sephira_awakening_bonuses import write_report
    write_report(catalog,names['PassiveSkill'])
