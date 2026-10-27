"""Equipable esper rewards. Definitions are global; effects require the wearer.

The harmless native continuous markers also appear through Spirit of Eiko.
They never grant summon commands or change the native esper/enemy definitions.
"""
import copy
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).with_name('esper_mastery.json')
PASSIVE = 'Skill/DT_PassiveSkillData'
EFFECT = 'Skill/DT_SkillEffectData'
IDS = frozenset((1960,1961,1962,1963))


@lru_cache(maxsize=1)
def data(): return json.loads(DATA.read_bytes())


def catalog(value):
    entries=[{'id':int(sid),'name':p['name'],'desc':p['desc'],'equipCost':p['cost'],
              'custom':True,'verified':False,'icon':'UI.Skill.Command.Icon.Passive'}
             for sid,p in data()['passives'].items()]
    existing={p['id'] for p in value.get('passives',[])}
    if existing & IDS: raise ValueError('An esper mastery ID overlaps the selected game catalog.')
    return {**value,'passives':[*value.get('passives',[]),*entries]}


def enabled(units):
    return any(g[0]=='PassiveSkill' and g[1] in IDS for u in units
               for field in ('awakening','synchro') for tier in u.get(field,[]) for g in tier)


def prepare(tables, rows, units):
    """Clone audited native operations, rejecting changed donors or occupied IDs."""
    if not enabled(units): return
    ps={p['ID']:(k,p) for k,p in rows(PASSIVE).items()}
    fx={p['ID']:(k,p) for k,p in rows(EFFECT).items()}
    pk,passive=ps[1316]
    def add(rel, op):
        tables.setdefault(rel,{'asset':'FFRS/Content/Datatable/'+rel,'add':[],'set':[]})['add'].append(op)
    def effect(identity, source, kind, params, **fields):
        key,original=fx[source]
        if identity in fx or original['EffectType']!=kind:
            raise ValueError('Native esper reward effect definitions changed; re-check this game build.')
        add(EFFECT,{'row':f'Studio_EsperEffect_{identity}','cloneFrom':key,
                    'set':{'ID':identity,'ParamList':params,**fields}})
    marker_source=fx[1402][1]
    if marker_source['ParamList'][:6] != [5,9,2,0,0,0]:
        raise ValueError('The native continuous marker template changed.')
    for raw,p in data()['passives'].items():
        sid=int(raw);eid=p['marker']
        if sid in ps: raise ValueError('An esper mastery ID overlaps the selected game catalog.')
        params=list(marker_source['ParamList']);params[0]=0
        effect(eid,1402,'ParameterContinuousVariation',params,proceedTiming='None',isUnremovable=True)
        bundles=copy.deepcopy(passive['effectBundleList'])
        bundles[0]['effectId']=eid
        for b in bundles[1:]:b['effectId']=-1
        add(PASSIVE,{'row':f'Studio_EsperPassive_{sid}','cloneFrom':pk,'set':{
            'ID':sid,'SortId':sid,'Name':p['name'],'Description':p['desc'],
            'equipCost':p['cost'],'effectBundleList':bundles,'bBattleOnly':True}})
    # A previously learned private equipment reward must remain resolvable in
    # an existing save, even though it is no longer offered by these MR ranks.
    import _ffr_sephira
    for retired in data()['retiredPassives']:
        sid=_ffr_sephira.private_passive_id(retired['preset'],retired['source'])
        if sid in ps:raise ValueError('A retired mastery ID overlaps the selected game catalog.')
        key,source=ps[retired['source']]
        add(PASSIVE,{'row':f'Studio_RetiredMastery_{sid}','cloneFrom':key,'set':{
            'ID':sid,'Name':retired['name'],'Description':retired['desc'],'equipCost':source['equipCost'] or 20}})
    # Exactly the native HP+20% operation. A one-shot recovery tops up the extra
    # health on the newly spawned actor, never on an existing damaged summon.
    effect(196201,16302,'ParameterContinuousVariation',list(fx[16302][1]['ParamList']),isUnremovable=True)
    damage=list(fx[12003][1]['ParamList']);damage[0]=20
    effect(196001,12003,'DamageMultiplier',damage,effectEndActionNum=-1,isUnremovable=True)
    # ParameterVariation: amount, HP/MP, percentage arithmetic. Apply now once;
    # neither resource recovery becomes a recurring self-turn regeneration.
    for identity,source,amount in ((196101,1019,5),(196202,21304,20)):
        original=fx[source][1]
        expected=[5,2,2] if source==1019 else [10,1,2]
        if (original['ParamList'][:3]!=expected or original['applyTiming']!='AddEffect'
                or original['proceedTiming']!='AddEffect' or original['effectEndActionNum']!=1):
            raise ValueError('The native immediate resource recovery template changed.')
        params=list(original['ParamList']);params[0]=amount
        effect(identity,source,'ParameterVariation',params)


def repair(unit):
    """CLI parity with Studio's reviewed migration, preserving private recipes."""
    member=unit.get('sephiraVision') or {};preset=member.get('preset')
    update=data()['kits'].get(preset)
    if not update or unit.get('sephiraKitRevision',0)>=update['kitUpdate']['version']:return
    plan=update['kitUpdate']
    for op in plan['mr']:
        kinds={'ActiveSkill','PassiveSkill',op['from'][0],op['to'][0]}
        choices=[g for g in unit['synchro'][op['rank']] if g[0] in kinds]
        if len(choices)!=1 or choices[0] not in (op['from'],op['to']):
            raise ValueError(f'{unit["en"]} MR{op["rank"]} was edited. Apply its kit update in Studio first.')
    result=copy.deepcopy(unit)
    if plan.get('mrOnly'):
        for op in plan['mr']:
            result['synchro'][op['rank']]=[list(op['to']) if g in (op['from'],op['to']) else g
                                         for g in result['synchro'][op['rank']]]
        result['sephiraKitRevision']=plan['version']
        unit.clear();unit.update(result)
        return
    owned=result['skills'];template=update['profile']
    def key(g):
        recipe=owned.get(str(g[1])) if g[0]=='ActiveSkill' else None
        return 'custom:'+str(recipe['from']) if recipe else f'{g[0]}:{g[1]}'
    awakening=[]
    for rank,tier in enumerate(template['awakening']):
        grants=[]
        for raw in tier:
            grant=list(raw);recipe=template['skills'].get(str(grant[1])) if grant[0]=='ActiveSkill' else None
            if recipe:
                matches=[int(s) for s,r in owned.items() if r['from']==recipe['from']]
                if len(matches)>1:raise ValueError('Choose one copy of '+recipe['en']+' before applying the kit update.')
                if matches:grant[1]=matches[0]
                else:
                    occupied={int(s)+d for s in owned for d in range(3)}
                    base=480000+(unit['id']-13450)*100
                    preferred=grant[1]+(unit['id']-template['id'])*100
                    target=next((s for s in [preferred,*range(base+3,base+96,3)]
                                 if not occupied.intersection((s,s+1,s+2))),None)
                    if target is None:raise ValueError('No space for the updated esper kit.')
                    value=copy.deepcopy(recipe);value['jp']+=f'_KitUpdate_{target}'
                    for field in ('belongCommandList','commandIdBelongDebuggingAllSkills'):
                        value['set'][field]=[unit['command']['id'] if v==template['command']['id'] else v for v in value['set'][field]]
                    owned[str(target)]=value;grant[1]=target
            grants.append(grant)
        grants.extend(g for g in result['awakening'][rank] if key(g) not in plan['managed'])
        if len(grants)>8:raise ValueError(f'{unit["en"]} tier {rank+1} has no room for its kit update.')
        awakening.append(grants)
    result['awakening']=awakening
    for op in plan['mr']:
        result['synchro'][op['rank']]=[list(op['to']) if g in (op['from'],op['to']) else g
                                     for g in result['synchro'][op['rank']]]
    result['sephiraPassiveText']=copy.deepcopy(template['sephiraPassiveText'])
    if result['master']['desc'] in plan['masterDescriptions']:result['master']['desc']=template['master']['desc']
    result['sephiraKitRevision']=plan['version']
    unit.clear();unit.update(result)
