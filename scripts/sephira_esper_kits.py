"""Reviewed Eiko esper mastery and Mog LB rewards; preserve save identities."""
import copy


PASSIVES = {
    1960: {'name': 'Esper Power', 'desc': 'Increase damage dealt by summoned espers by 20%.', 'cost': 30},
    1961: {'name': 'Esper Communion', 'desc': 'Restore 5% of the summoner’s max MP whenever their esper acts.', 'cost': 20},
    1962: {'name': 'Enduring Eidolons', 'desc': 'Summoned espers gain 20% max HP and one extra action before their final special.', 'cost': 40},
    1963: {'name': 'Eidolon Revelry', 'desc': 'Each ordinary esper action has a 30% chance to become its special. The final special is guaranteed.', 'cost': 50},
}
REWARDS = {'eiko': [('PassiveSkill',1107),('PassiveSkill',1960),('PassiveSkill',1961),('PassiveSkill',1962),('PassiveSkill',1963)],
           'mog': [('ActiveSkill',400460),('PassiveSkill',1049),('PassiveSkill',1338),('PassiveSkill',1498),('PassiveSkill',1031)]}


def revise(catalog):
    for preset in catalog['presets']:
        if preset['id'] not in {*REWARDS,'mystea'}: continue
        unit = preset['profile']
        if unit.get('sephiraKitRevision',0) >= 1: continue
        old = copy.deepcopy(unit)
        preset['esperKitBefore'] = old
        managed = set()
        if preset['id'] == 'eiko':
            for tier in unit['awakening']:
                tier[:] = [g for g in tier if g[:2] not in (['ActiveSkill',430990],['ActiveSkill',431000])]
            for sid, source, name, desc, cost, rank, extra in (
                (486545,215000,'Healing Light','Restore a small amount of HP for all allies.',12,0,{'TargetType':'Group','isApplyAllMag':False,'skillIdAfterModeChange':-1}),
                (486548,210050,'Eidolon’s Reprieve','Grant Regen to all allies.',25,1,{'TargetType':'Group','isApplyAllMag':False,'skillIdAfterModeChange':-1}),
            ):
                assert str(sid) not in unit['skills']
                unit['skills'][str(sid)] = {'from':source,'visuals':source,'jp':f'Sephira_eiko_EsperKit_{sid}',
                    'en':name,'desc':desc,'descAuto':False,'set':{'Cost':cost,'belongCommandList':[unit['command']['id']],
                    'commandIdBelongDebuggingAllSkills':[unit['command']['id'],-1],**extra}}
                unit['awakening'][rank].insert(2,['ActiveSkill',sid,-1])
            for rank, previous, replacement in ((2,1277,1045),(3,1455,1256)):
                grant = next(g for g in unit['awakening'][rank] if g[:2] == ['PassiveSkill',previous])
                grant[1] = replacement
            unit['sephiraPassiveText'] = {str(sid):{k:v for k,v in text.items() if k!='cost'} for sid,text in PASSIVES.items()}
            preset['theme'] = 'Esper mastery, wind magic and healing'
        elif preset['id']=='mog':
            unit['sephiraPassiveText'] = {'1498':{'name':'Peaceful LB Engine','desc':'Fill the LB gauge by 10% when acting without dealing damage.'}}
        for field in ('awakening',):
            for version in (old,unit):
                for tier in version[field]:
                    for kind, sid, *_ in tier:
                        recipe = version['skills'].get(str(sid)) if kind=='ActiveSkill' else None
                        managed.add('custom:'+str(recipe['from']) if recipe else f'{kind}:{sid}')
        operations=[]
        for rank, (kind,sid) in zip((1,3,5,7,9),REWARDS.get(preset['id'],[])):
            previous=next(g for g in old['synchro'][rank] if g[0] in ('ActiveSkill','PassiveSkill'))
            new=[kind,sid,-1]
            unit['synchro'][rank]=[new if g==previous else g for g in unit['synchro'][rank]]
            if previous!=new:operations.append({'rank':rank,'from':previous,'to':new})
        if preset['id']=='mystea':
            for rank,other in ((1,2),(2,1),(5,9),(9,5)):
                previous=old['synchro'][rank][0];new=copy.deepcopy(old['synchro'][other][0])
                unit['synchro'][rank][0]=new
                operations.append({'rank':rank,'from':previous,'to':new})
        description=f"Grants all of {preset['name']}'s mastery abilities."
        unit['master']['desc']=description
        unit['sephiraKitRevision']=1
        preset['kitUpdate']={'version':1,'managed':sorted(managed),'mr':operations,
                             'masterDescriptions':[old['master']['desc']]}
        balance=preset['balance']
        balance['activeCount']=sum(g[0]=='ActiveSkill' for tier in unit['awakening'] for g in tier)
        balance['passiveCount']=sum(g[0]=='PassiveSkill' for tier in unit['awakening'] for g in tier)
        balance['kitCount']=sum(map(len,unit['awakening']))
        balance['totalSkillCount']=balance['kitCount']+5
    eiko = next(p for p in catalog['presets'] if p['id'] == 'eiko')
    unit = eiko['profile']
    if unit.get('sephiraKitRevision', 0) < 2:
        raise_grant = ['ActiveSkill', 210140, -1]
        unit['awakening'][1].remove(raise_grant)
        unit['awakening'][0].insert(3, raise_grant)
        unit['awakening'][1].insert(1, ['ActiveSkill', 230070, -1])
        unit['sephiraKitRevision'] = 2
        eiko['kitUpdate']['version'] = 2
        eiko['kitUpdate']['managed'] = sorted({*eiko['kitUpdate']['managed'], 'ActiveSkill:230070'})
        balance = eiko['balance']
        balance['activeCount'] += 1
        balance['kitCount'] += 1
        balance['totalSkillCount'] += 1
    return catalog


if __name__=='__main__':
    import json
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'assets/sephira_visions/catalog.json'
    path.write_text(json.dumps(revise(json.loads(path.read_bytes())),indent=2)+'\n')
