"""Apply the user's reviewed Crystal Fina/Aria layouts from 2026-10-25.

Keep the existing namespaces, skill mechanics, MR stat budgets and acquisitions.
The original 0-MP Reraise follow-up is replaced by its native castable spell.
"""
import copy


LAYOUTS = {
    'crystal_fina': [
        [('ActiveSkill',210010),('ActiveSkill',210250),('custom',570690),('ActiveSkill',230040),('ActiveSkill',210140),('PassiveSkill',1381),('PassiveSkill',1107)],
        [('ActiveSkill',210020),('ActiveSkill',210260),('custom',503630),('custom',501930),('custom',506110),('ActiveSkill',230050),('ActiveSkill',210130),('PassiveSkill',1277)],
        [('ActiveSkill',210030),('ActiveSkill',210270),('ActiveSkill',210150),('custom',503210),('custom',215020),('custom',240190),('PassiveSkill',1455)],
        [('custom',210190),('ActiveSkill',210160),('PassiveSkill',1456)],
    ],
    'aria': [
        [('ActiveSkill',420100),('ActiveSkill',220480),('custom',245000),('custom',502020),('custom',225090),('custom',503970),('ActiveSkill',210120),('PassiveSkill',1375)],
        [('ActiveSkill',420110),('ActiveSkill',220490),('ActiveSkill',414500),('custom',245010),('custom',501400),('custom',501680),('ActiveSkill',210140),('PassiveSkill',1111)],
        [('ActiveSkill',420120),('ActiveSkill',220500),('custom',501440),('custom',250130),('ActiveSkill',210130),('PassiveSkill',1300),('PassiveSkill',1301)],
        [('ActiveSkill',210160),('PassiveSkill',1352)],
    ],
}


def grant_key(unit, grant):
    recipe=unit.get('skills',{}).get(str(grant[1])) if grant[0]=='ActiveSkill' else None
    return ('custom' if recipe else grant[0])+':'+str(recipe['from'] if recipe else grant[1])


def revise(catalog):
    for preset in catalog['presets']:
        key=preset['id']
        if key not in LAYOUTS:continue
        description=f"Grants all of {preset['name']}'s mastery abilities."
        old_descriptions=[f"{preset['name']}'s learned mastery rewards flow into the wearer."]
        if key=='crystal_fina':old_descriptions.append("Crystal Fina's resonance flows into the wearer.")
        preset['profile']['master']['desc']=description
        unit=preset['profile'];owned=unit['skills']
        managed=set(preset.get('kitUpdate',{}).get('managed',[])) | {grant_key(unit,g) for tier in unit['awakening'] for g in tier}
        # The user's draft selected the internal revive event rather than the
        # 40-MP spell. Cover that draft as well as the previous custom copy.
        if key=='crystal_fina':managed.add('ActiveSkill:210240')
        desired=[]
        for tier in LAYOUTS[key]:
            grants=[]
            for kind,source in tier:
                managed.add(kind+':'+str(source))
                identity=source
                if kind=='custom':
                    identity,= [int(sid) for sid,r in owned.items() if r['from']==source]
                grants.append(['ActiveSkill' if kind=='custom' else kind,identity,-1])
            desired.append(grants)
        unit['awakening']=desired
        # Keep retired definitions for older learned-skill/save references;
        # only the four learned tiers determine the new available kit.
        preset['kitUpdate']={'version':1,'managed':sorted(managed),'masterDescriptions':old_descriptions}
        unit['sephiraKitRevision']=1
        if key=='aria':
            for tier in unit['synchro']:
                for g in tier:
                    if g[:2]==['PassiveSkill',1527]:g[1]=1524
            unit['sephiraPassiveText'].pop('1527',None)
            unit['sephiraPassiveText']['1524']={'name':'Imbue Water','desc':'Add water to non-elemental standard attacks and battle skills.'}
            preset['kitUpdate']['passiveReplacement']=[1527,1524]
            preset['masteryCuration']['extraPassives']=[1524]
            preset['balance']['additionalPassives']=[1524]
            next(g for g in preset['awakeningBalance']['grants'] if g['id']==1111)['rank']=1
            preset['theme']='Water magic, water blades and healing'
        # Refresh only the audit derived from the edited learned list.
        balance=preset['balance']
        balance['activeCount']=sum(g[0]=='ActiveSkill' for tier in desired for g in tier)
        balance['kitCount']=sum(map(len,desired))
        balance['totalSkillCount']=balance['kitCount']+balance['mrSkillCount']
        for recipe in balance['playerCopies']:
            recipe['unlock']=next(([field,rank] for field in ('awakening','synchro') for rank,tier in enumerate(unit[field])
                                  if any(g[:2]==['ActiveSkill',recipe['id']] for g in tier)),None)
    catalog['passiveCuration']['distinctCount']=len({g[1] for p in catalog['presets'] for tier in p['profile']['synchro'] for g in tier if g[0]=='PassiveSkill'})
    return catalog


def standalone(profile,catalog):
    """Keep independent Fina's identity/artwork/acquisition and MR grants."""
    result=copy.deepcopy(profile)
    if result.get('sephiraKitRevision',0)>=1:return result
    template=next(p['profile'] for p in catalog['presets'] if p['id']=='crystal_fina')
    # Independent Fina uses the same source recipes in a different namespace.
    desired=[]
    for tier in LAYOUTS['crystal_fina']:
        grants=[]
        for kind,source in tier:
            identity=source
            if kind=='custom':
                existing=[int(sid) for sid,r in result['skills'].items() if r['from']==source]
                if existing:identity,=existing
                else:
                    original,recipe=next((int(sid),r) for sid,r in template['skills'].items() if r['from']==source)
                    preferred=original+(result['id']-template['id'])*100
                    occupied={int(sid)+delta for sid in result['skills'] for delta in range(3)}
                    identity=next(sid for sid in [preferred,*range(480000+(result['id']-13450)*100+3,480000+(result['id']-13450)*100+96,3)]
                                  if all(sid+delta not in occupied for delta in range(3)))
                    value=copy.deepcopy(recipe)
                    value['jp']=f"{value['jp']}_Independent_{identity}"
                    for field in ('belongCommandList','commandIdBelongDebuggingAllSkills'):
                        value['set'][field]=[result['command']['id'] if v==template['command']['id'] else v for v in value['set'][field]]
                    result['skills'][str(identity)]=value
            grants.append(['ActiveSkill' if kind=='custom' else kind,identity,-1])
        desired.append(grants)
    result['awakening']=desired
    result['sephiraKitRevision']=1
    result['master']['desc']=template['master']['desc']
    return result
