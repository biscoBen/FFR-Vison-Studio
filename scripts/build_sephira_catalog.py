"""Reproduce the balanced presets from audited native tables and selected FFBE packs.

Developer tool only; the app ships the resulting catalog, not the private inputs.
Usage: python scripts/build_sephira_catalog.py --reference /path/to/ffr/runtime
"""
import argparse
import copy
import json
from pathlib import Path
from sephira_kit_expansion import EXPANSIONS, AWAKENING_EXPANSIONS, PLAYER_EFFECT_REPLACEMENTS

ROOT = Path(__file__).resolve().parents[1]

# Known, actor-independent spell/attack presentations. Prefer an available
# source sequence; otherwise borrow a native spell of the same element/tier.
SPELLS = {'Fire':220010,'Ice':220050,'Thunder':220090,'Water':220130,
          'Wind':220170,'Earth':220210,'Light':210250}
SUPPORT = {
    210240:'Grant Reraise to an ally.', 400790:'Choose a physical and magic counter; reduce incoming damage this turn.',
    502470:'Reduce enemy physical and magic defense by 30% for 3 turns.',
    500860:'Reduce party physical and magic damage taken by 30%.',
    500700:'Raise own physical evasion by 50%.',
    502080:'Raise own defenses while lowering attack and magic.',
    501700:'Raise own attack and magic by 50%, lowering both defenses.',
    501120:'Raise party magic and speed by 50%.',
    570130:'Raise an ally’s attack/magic by 50% and reduce incoming physical/magic damage by 30%.',
    505560:'Reduce enemy physical and magic defense by 30% for 3 turns.',
    505570:'Reduce party physical and magic damage taken by 30%.',
    502230:'Also raise own attack by 50%.', 502370:'Also reduce own physical/magic damage taken by 30%.',
    505410:'Also defend after attacking.', 501400:'Also reduce enemy physical and magic defense.',
    501420:'Also reduce enemy physical and magic defense.',
    505960:'Also reduce enemy physical and magic defense.',
    505910:'Also reduce enemy attack and magic.',
    501780:'Raise own attack and magic by 50% for 3 turns.',
    502710:'Raise an ally’s magic by 50% for 3 turns.',
    502730:'Raise an ally’s attack by 50% for 3 turns.',
    501340:'Also reduce own physical damage taken by 30% for 3 turns.',
    500930:'Also reduce own physical damage taken by 30% for 3 turns.',
    505420:'Reduce own physical damage taken by 30% for 3 turns.',
    505430:'Reduce own magic damage taken by 30% for 3 turns.',
    505530:'Reduce own physical and magic damage taken by 30% for 3 turns.',
    505360:'Remove party ailments and stat debuffs.',
    570690:'Remove an ally’s ailments.',
    571330:'Also remove enemy buffs.', 571140:'Also remove enemy buffs.',
    571520:'Remove own ailments/debuffs and gain 30% physical/magic protection for 3 turns.',
    503170:'Attempt to lower enemy attack, magic, defenses and speed.',
    503670:'Also lower enemy physical attack and defense.',
    503680:'Also lower enemy magic and magic defense.',
    506040:'Also remove enemy buffs.',
}


def place_grant(unit, kind, sid, pool, preferred):
    """Keep native unlocks; spread new utility/power over awakening and MR."""
    options = pool.get((kind,sid))
    if options:
        aw=[r for f,r in options if f=='awakening']
        field,rank=('awakening',min(aw)) if aw else ('synchro',min(r for f,r in options))
        candidates=[(field,rank)]
    else:
        field,rank=preferred
        candidates=[(field,rank)]
        if field=='awakening':
            candidates += [('awakening',r) for r in range(rank+1,4)]
        candidates += [('synchro',r) for r in [7,9,5,3,1]]
    for field,rank in candidates:
        if len(unit[field][rank]) < (8 if field=='awakening' else 5):
            unit[field][rank].append([kind,sid,-1]); return field,rank
    raise ValueError(f"{unit['key']}: no room for {kind} {sid}")


def player_recipe(unit, slot, spec, native, english, effects):
    source,name,mp,overrides=spec
    original=native[source]
    settings={'Cost':mp, 'accuracy':min(original['accuracy'],100),
              'belongCommandList':[unit['command']['id']],
              'commandIdBelongDebuggingAllSkills':[unit['command']['id'],-1],
              # Enemy group-toggle partners must not bypass this copy's cost.
              'skillIdAfterModeChange':-1, 'isApplyAllMag':False,
              'playSequencerId':-1, 'sequencerIdWhenTargetFriendlies':-1,
              'voiceLabel':'None', 'selfSkillActivateVoiceLabel':'None',
              **overrides}
    if source in PLAYER_EFFECT_REPLACEMENTS or source==500930:
        # Finite native player effects replace boss-only or excessive effects.
        bundles=copy.deepcopy(original['effectBundleList'])
        for b in bundles:
            b['effectId']=PLAYER_EFFECT_REPLACEMENTS.get(source,{}).get(b['effectId'],b['effectId'])
            if source==501340 and b['effectId']==1042:
                b.update(TargetType='Self',targetRelation='Friendlies')
        if source==500930:
            b=bundles[0]; b.update(effectId=1042,TargetType='Self',targetRelation='Friendlies')
        settings['effectBundleList']=bundles
    if 'hitCount' in overrides:
        n=overrides['hitCount']
        # Integer percentages total 100%, with stable native float readback.
        settings['hitDamageRatioList']=[(100//n+(i<100%n))/100 for i in range(n)]+[0.0]*(len(original['hitDamageRatioList'])-n)
    effective={**original,**settings}
    sid=445000+(unit['id']-13100)*100+slot*3
    vis=source
    if not english[source]['seq']:
        element=effective['element']; power=effective['magnification']
        if effective['parameterVariationType']=='Increase' and effective['parameterType']=='HitPoint':
            vis=210010 if power<=200 else 210020 if power<=600 else 210030
        elif element in SPELLS:
            vis=SPELLS[element]+(20 if power>40 else 10 if power>20 else 0)
            if not english.get(vis,{}).get('seq'): vis=SPELLS[element]
            if effective['DamageType']=='Physic' and element in ['Earth','Thunder']:
                vis=(420160 if element=='Earth' else 420070)+(20 if power>40 else 10 if power>20 else 0)
        elif effective['DamageType']=='Physic': vis=400530
        elif effective['element']=='Dark': vis=408050
        else: vis=400630
    desc=[]
    if effective['skillEffectType']=='DamageAndRecovery':
        heal=effective['parameterVariationType']=='Increase'
        calc=effective['damageCalcType']; power=effective['magnification']
        if heal:
            amount=f'{power}% max HP' if calc in ['TargetMaxHPRatio','SelfMaxHPRatio'] else f'{power} HP' if calc=='Fixed' else f'healing power {power}'
            desc.append('Restore '+amount+'.')
        elif calc=='MPAbsorb': desc.append(f'Drain MP; power {power}.')
        else: desc.append(f"{effective['element'] if effective['element']!='None' else 'Non-elemental'} {'physical' if effective['DamageType']=='Physic' else 'magic'} damage; power {power}.")
    if source in SUPPORT: desc.append(SUPPORT[source])
    else:
        labels=[]
        for b in effective['effectBundleList']:
            e=effects.get(b['effectId'])
            if not e: continue
            if e['status']!='None': labels.append(f"{e['status']} ({e['prob']}%)")
            elif e['type']=='DamageAbsorb': labels.append(f"{'HP' if e['params'][0]==0 else 'MP'} drain ({e['params'][1]}% of damage)")
        if labels: desc.append('Apply '+', '.join(dict.fromkeys(labels))+'.')
    # Retain native description for otherwise unclassified support, not its
    # placeholder statistics. The numbers below always describe the copy.
    if not desc: desc.append(english[source]['desc'].split('. ')[0].rstrip('.')+'.')
    desc.append(f"{effective['TargetType']} {effective['defaultTargetRelation'].lower()}; MP {mp}; hits {effective['hitCount']}; accuracy {effective['accuracy']}; stagger {effective['breakDamageValue']}.")
    recipe={'from':source,'visuals':vis,'jp':f"{unit['jp']}_Kit_{slot}",
            'en':name,'desc':' '.join(desc),'descAuto':False,'set':settings}
    unit['skills'][str(sid)]=recipe
    return sid, {'id':sid,'source':source,'name':name,'originalName':english[source]['name'],
                 'sourceCategory':'enemy' if 500000<=source<600000 or 240000<=source<260000 else 'native',
                 'original':{k:original[k] for k in settings},'adjusted':settings,
                 'combat':{k:effective[k] for k in ['Cost','magnification','DamageType','damageCalcType',
                           'element','TargetType','defaultTargetRelation','parameterVariationType',
                           'hitCount','breakDamageValue']},
                 'effects':[b['effectId'] for b in effective['effectBundleList'] if b['effectId']>0]}

# Exact native IDs, deliberately allocated once within this collection.
# Requested specialties take priority over the source game's automatic role labels.
# id, title, selected form, theme, native stat/MR budget, active IDs, passive IDs
PLANS = [
 ('a2', 'A2', '310000505', 'Physical combo attacker', 13116,
  [446600,446610,400300,400690,400710,400500], [1421,1422,1423,1424,1105,1378,1309]),
 ('christine','Christine','401002606','Ice magic and stagger',13024,
  [220050,220060,220070,400630,230030,210200], [1406,1376,1285,1281,1033,1407,1045]),
 ('crystal_fina','Crystal Fina','99887755552703','Healing, cleansing and light magic',13051,
  [210010,210020,210030,210250,210260,210270,210130,210150,400740], [1283,1375,1455,1456,1393,1397]),
 ('barusa','Barusa','401003006','Earth physical bruiser and protection',13062,
  [421400,421410,421420,421340,421350,421360,414700,414710,400640], [1452,1453,1454,1313,1379,1336]),
 ('fran','Blue Sky Belle Fran','212001706','Ranged physical and disabling arrows',13101,
  [421250,421260,421270,421100,421110,421120,422010,422030,400450], [1128,1125,1126,1321,1337,1443]),
 ('lunafreya','Oracle Maiden Lunafreya','215002417','Debuff specialist with water/wind magic',13118,
  [446800,446810,446820,446830,446860,446870,230080,230090], [1425,1468,1131,1132,1326,1396]),
 ('minfilia','Minfilia','214000304','Mixed earth/wind offense and party protection',13102,
  [220210,220220,220230,445200,445210,400240,230040,230050], [1410,1411,1412,1311,1465,1343,1362]),
 ('folka','Folka','100018306','Water magic with restorative utility',13024,
  [220130,220140,220150,220310,210050,414510,400680,400360], [1251,1348,1367,1380,1307,1445]),
 ('fryevia','Fryevia','302001405','Ice spellblade and precision physical',13105,
  [421070,421080,421090,420270,400350], [1414,1415,1416,1357,1363,1344]),
 ('lenneth','Lenneth','330000106','Physical cover tank with light attacks',13100,
  [445010,445020,445030,420330,420340,420350,400390], [1408,1409,1029,1290,1042,1331]),
 ('lila','Lila','100013806','Martial physical damage and self recovery',13101,
  [421010,421020,421030,445100,445110,445120,400440,400650], [1353,1288,1077,1273,1325,1284,1286]),
 ('mystea','Mystea','100011005','Magic tank, barriers and counter magic',13103,
  [230060,230070,230120,220410,220510], [1315,1073,1395,1299,1030,1291,1402]),
 ('reberta','Reberta (JP)','100014405','Dragoon with fire/wind spear attacks',13130,
  [400210,421040,421050,421060,421310,421320,421330,400670,448000,448010], [1257,1360,1320,1335,1359,1437,1442,1460]),
 ('snow_white','Snow White','336000207','Dark physical drain and risk/reward',13103,
  [422040,420300,420310,420320,400490,422020,220300], [1457,1405,1431,1358,1318,1293]),
 ('aria','Aria','203000905','Water support, healing and water blade',13045,
  [420100,420110,420120,220480,220490,220500,414500,400550], [1282,1352,1401,1305,1462,1356]),
 ('eiko','Eiko','209000707','Summoner with wind magic and revival',13051,
  [430990,431000,220450,220460,220470,210140,210160], [1031,1338,1107,1111,1047,1000,1417]),
 ('alice','Alice/Half Nightmare','336000127','Ice physical with burst and HP tradeoffs',13116,
  [421370,421380,421390,446300,446310,400530], [1234,1388,1247,1330,1106,1294]),
 ('mog','Moogle of Narshe Mog','206003005','Wind magic, dance and speed support',13120,
  [220170,220180,220190,230130,230140,230150,230160,400760], [1248,1316,1277,1292,1287,1049]),
 ('lilith','Lilith','401005905','Dark counter tank and protective magic',13103,
  [220390,220520,220400,445310,400380,414600,414610], [1413,1333,1339,1369,1253,1300]),
 ('freya','Dragon Knight Freya','209001805','Aerial light physical and water lance',13128,
  [447810,447800,421190,421200,421210,400280], [1361,1466,1116,1340,1438,1394]),
 ('trance_terra','Trance Terra','206000125','Dark/fire magic, poison and costly finishers',13123,
  [447300,447310,220250,220260,220320,220350,400730,220380,220340,220010,220020,220030], [1432,1433,1275,1381,1319,1351,1038]),
 ('ariana','Charming Kitty Ariana','401002405','Healing singer with control and arcane attacks',13051,
  [210120,400540,400460,230100,230180,220280,220290], [1464,1392,1391,1114,1109,1301]),
 ('elephim','Elephim','100017107','Buff/debuff bard with ranged attacks',13124,
  [230190,230020,230110,414200,414210,230170], [1296,1297,1295,1451,1372,1235]),
 ('jade','Jade','337001205','Lightning martial attacker and crowd damage',13110,
  [420070,420080,420090,421160,421170,421180,400310,400700], [1323,1250,1366,1371,1385,1308]),
 ('primm','Spirited Heart Primm','304000717','Mixed elemental sabers and support',13102,
  [421280,421290,421300,420160,420170,420180,445300,400660,400770], [1310,1370,1355,1461,1390,1011]),
 ('relm','Relm','206001005','Painter with lightning magic and mimicry',13123,
  [220090,220100,220110,220330,400330,400720], [1104,1237,1280,1279,1332,1328]),
 ('rikku','Rikku (FFX-2)','249000206','Thief, item utility and fire physical breaks',13124,
  [400260,400270,400750,446840,446850,400400,400250,447400,447410], [1426,1056,1387,1435,1436,1386,1050]),
 ('nalu','Nalu','100015405','Lightning physical, criticals and analysis',13110,
  [446000,446010,421130,421140,421150,210220,447500,447510], [1420,1418,1399,1347,1400,1124]),
 ('elza','Elza','302000605','Dark/water physical and sustained pressure',13120,
  [422050,422060,422070,447000,447010,447020,421220,421230,421240], [1428,1434,1317,1350,1403,1389]),
 ('lunera','Lunera','100007506','Wind physical and stagger support',13105,
  [420130,420140,420150,445500,445510,414400,414410], [1458,1448,1449,1341,1066,1258]),
]


def generate(reference):
    rows_dir = reference / 'unverified-export/extracted/rows'
    cache={}
    def rows(name):
        if name not in cache: cache[name]=json.loads((rows_dir / (name + '.json')).read_text())['rows']
        return cache[name]
    def by_id(name, id): return next(v for v in rows(name).values() if v['ID'] == id)
    english=json.loads((reference/'user-animation-reference/inspection/data/ffr_catalog.json').read_text())
    skill_names={x['id']:x for x in english['skills']}
    effects={x['id']:x for x in english['effects']}
    skill_rows={v['ID']:v for v in rows('Skill/DT_SkillData').values()}
    hidden={s['id'] for s in json.loads((ROOT/'assets/existing_visions/payload/ability_hiding_review.json').read_text())['skills']}
    native = {v['id']: v for v in json.loads((reference/'native-kit-audit.json').read_text())['checked']}
    reservations={key: sorted({v['ID'] for v in rows(rel).values()}) for key,rel in [
        ('visions','Item/Vision/DT_VisionItemData'),('units','Unit/DT_UnitParameter'),
        ('commands','Skill/DT_CommandSkillData'),('masters','Skill/DT_MasterSkillData'),
        ('skills','Skill/DT_SkillData')]}
    pool = {}
    for u in native.values():
        for field in ['awakening','synchro']:
            for rank, tier in enumerate(u[field]):
                for g in tier:
                    if g[0] in ['ActiveSkill','PassiveSkill']:
                        pool.setdefault((g[0],g[1]),[]).append((field,rank))
    host = json.loads((reference/'sephira-research/host-index.json').read_text())
    presets=[]; assigned={}
    for i, (key,title,form,theme,budget,actives,passives) in enumerate(PLANS):
        # Keep 13520 (the retired Great Dragon slot) out of preferred IDs so
        # every later preset retains its original identity.
        vid=13500+i+(1 if i>=20 else 0)
        stats=by_id('Unit/DT_UnitParameter',budget)
        stats={k:stats[k] for k in ['MaxHitPoint','MaxMagicPoint','Attack','Defence','Intelligence','Mind','Agility']}
        attack = 'Magic' if key in ['christine','crystal_fina','folka','mystea','eiko','trance_terra','ariana','elephim','relm','lunafreya','mog','aria'] else 'Physic'
        # Use an existing physical/magic level curve and sprite template; base
        # stats and permanent MR awards come from the declared native budget.
        donor = 13108 if attack=='Magic' else 13110
        if key in ['minfilia','primm']: donor=13125
        unit={'key':'sephira_'+key,'id':vid,'sort':vid+70,'jp':'Sephira_'+key,
              'en':title,'desc':theme+'. A Sephira vision with native-budget Resonance skills.',
              'donor':donor,'attackType':attack,'stats':stats,'roles':['eUnitRole::'+('Healer' if key in ['crystal_fina','aria','ariana'] else 'Defender' if key in ['lenneth','mystea','lilith'] else 'Jammer' if key in ['lunafreya','elephim'] else 'Attacker')],
              'elemRes':{},'command':{'id':320+vid-13500,'en':title+' Skills','desc':theme+'.'},
              'master':{'id':vid*100,'en':'Spirit of '+title,'desc':title+"'s learned mastery rewards flow into the wearer."},
              'price':1000,'skills':{},'ffbeMap':{'skills':{},'passives':{}},'menuScale':2.0,
              'sephiraRecipe':3,
              'awakening':[[],[],[],[]], 'synchro':[[] for _ in range(10)]}
        if key=='crystal_fina':
            original=json.loads((ROOT/'assets/crystal_fina/profile.json').read_text())
            unit.update({k:copy.deepcopy(original[k]) for k in ['ffbe','custom','menuScale','icon']})
            unit['bundledPreset']='custom.crystal_fina.v1'
            lb=copy.deepcopy(original['lb_custom'])
        else:
            record=host['unitBundles'][form]
            h=next(u for u in host['units'] if form in u['forms'])
            detail=json.loads((reference/'sephira-research/selected/unit_records'/f"{record['unitId']}.json").read_text())['detail']
            unit['ffbe']={'id':form,'base':record['unitId'],'source':detail['region'],'dir':f'units/ffbe/sephira_{key}/sprites/{form}'}
            shift=h.get('shift',{}).get(form)
            if shift:
                unit['ffbe'].update({'baseForm':shift['base'],'baseDir':f"units/ffbe/sephira_{key}/sprites/{shift['base']}", 'shift':shift['kind']})
            lb={'from':by_id('Item/Vision/DT_VisionItemData',budget)['finishBlowSkill'],
                'presentation':'ffbe','mechanics':'custom','audio':'none','visuals':440110,
                'clone_sequence':True,'mute':['VO_'],'field_color_mode':'element',
                'ffbe_lb_id':form,'movement':{'enabled':False},'set':{}}
        # Element/type changes express the requested role without increasing the
        # native total multiplier, adding effects, or lowering costs.
        lb_overrides = {
            'a2': {'element':'None'}, 'alice':{'element':'Ice'}, 'fran':{'element':'Wind'},
            'lunafreya':{'element':'Water'}, 'folka':{'element':'Water'},
            'fryevia':{'element':'Ice'}, 'snow_white':{'element':'Dark'},
            'freya':{'element':'Water'}, 'relm':{'element':'Thunder'},
            'elza':{'element':'Dark'},
            'mog':{'element':'Wind','DamageType':'Magic','damageCalcType':'Magic'},
        }
        if key in ['mystea','elephim']: lb['from']=412620
        if key=='eiko': lb['from']=440090; lb_overrides[key]={'element':'Light'}
        lb.setdefault('set',{}).update(lb_overrides.get(key,{}))
        lb.update({'jp':'Sephira_'+key+'_Resonance','en':title+' Resonance',
                   'desc':'Native '+native[budget]['name']+' resonance mechanics; '+title+"'s own sprite animation.", 'descAuto':False,'nameAuto':False})
        unit['lb']=lb['from']; unit['lb_custom']=lb
        for kind, ids in [('ActiveSkill',actives),('PassiveSkill',passives)]:
            for sid in ids:
                if (kind,sid) in assigned: raise ValueError(f'Duplicate {kind} {sid}: {key}, {assigned[kind,sid]}')
                assigned[kind,sid]=key
                options=pool.get((kind,sid),[('awakening',2)])
                aw=[r for f,r in options if f=='awakening']
                field,rank=('awakening',min(aw)) if aw else ('synchro',min(r for f,r in options))
                unit[field][rank].append([kind,sid,-1])
        # Dual Jobs selects a vision by ID; use a private native-equivalent copy
        # rather than changing the original Onion Knight skill globally.
        if 445210 in actives:
            sid=445000+(vid-13100)*100+90
            unit['skills'][str(sid)]={'from':445210,'visuals':445210,
                'jp':'Sephira_'+key+'_DualJobs','en':'Dual Jobs',
                'desc':'Use Blade Torrent and another Minfilia skill in one turn.',
                'set':{'mimicableUnitId':vid}}
            for tier in unit['awakening']:
                for g in tier:
                    if g[:2]==['ActiveSkill',445210]: g[1]=sid
        extra_actives,extra_passives=EXPANSIONS[key]
        additions=[]
        for slot,spec in enumerate(extra_actives,1):
            source=spec[0]
            if source in hidden: raise ValueError(f'{key}: hidden source {source}')
            if ('ActiveSkill',source) in assigned: raise ValueError(f'{key}: duplicate added active {source}')
            assigned['ActiveSkill',source]=key
            sid,copy_audit=player_recipe(unit,slot,spec,skill_rows,skill_names,effects)
            # Lookup source unlocks before replacing its identity with a copy.
            mp=spec[2]; tier=0 if mp<=12 else 1 if mp<=24 else 2 if mp<=40 else 3
            field,rank=place_grant(unit,'ActiveSkill',source,pool,('awakening',tier))
            unit[field][rank][-1][1]=sid
            copy_audit['unlock']=[field,rank]; additions.append(copy_audit)
        for n,sid in enumerate(extra_passives):
            if ('PassiveSkill',sid) in assigned: raise ValueError(f'{key}: duplicate added passive {sid}')
            assigned['PassiveSkill',sid]=key
            place_grant(unit,'PassiveSkill',sid,pool,('synchro',3 if n==0 else 7))
        if key=='alice':
            # Aileen's earth slams were thematic placeholders in revision 1.
            # Keep native multipliers/costs; express Alice's ice specialization.
            for slot,source in enumerate([421370,421380,421390],20):
                sid,copy_audit=player_recipe(unit,slot,(source,['Ice Slam','Icera Slam','Icega Slam'][slot-20],skill_rows[source]['Cost'],{'element':'Ice'}),skill_rows,skill_names,effects)
                for tier in unit['awakening']:
                    for g in tier:
                        if g[:2]==['ActiveSkill',source]: g[1]=sid
                additions.append(copy_audit)
        awakening_actives,awakening_passives=AWAKENING_EXPANSIONS[key]
        for kind,entries in [('ActiveSkill',awakening_actives),('PassiveSkill',awakening_passives)]:
            for n,entry in enumerate(entries):
                source=entry[0] if kind=='ActiveSkill' else entry
                if kind=='ActiveSkill' and source in hidden: raise ValueError(f'{key}: hidden awakening source {source}')
                if (kind,source) in assigned: raise ValueError(f'{key}: duplicate awakening source {kind} {source}')
                assigned[kind,source]=key
                options=[r for f,r in pool.get((kind,source),[]) if f=='awakening']
                tier=min(options) if options else (0 if entry[2]<=12 else 1 if entry[2]<=24 else 2 if entry[2]<=40 else 3) if kind=='ActiveSkill' else 3
                sid=source
                if kind=='ActiveSkill':
                    sid,copy_audit=player_recipe(unit,10+n,entry,skill_rows,skill_names,effects)
                # No MR fallback: this revision must meet the awakening quota
                # independently, without moving or counting any MR rewards.
                available=[tier] if options else list(range(tier,4))+list(range(tier-1,-1,-1))
                rank=next((r for r in available if len(unit['awakening'][r])<8),None)
                if rank is None: raise ValueError(f'{key}: no awakening room for {kind} {source}')
                unit['awakening'][rank].append([kind,sid,-1])
                if kind=='ActiveSkill':
                    copy_audit['unlock']=['awakening',rank]; additions.append(copy_audit)
        # Stat rewards are copied exactly, including ranks, AP and totals.
        for rank,tier in enumerate(native[budget]['synchro']):
            unit['synchro'][rank].extend(copy.deepcopy([g for g in tier if g[0]=='BaseParameter']))
        unit['synchro'][9].append(['MasterSkill',vid*100,-1])
        checks={'visions':{vid},'units':{vid},'commands':{unit['command']['id']},
                'masters':{unit['master']['id']},
                'skills':{int(s) for s in unit['skills']} | {440000+(vid-13099)*10}}
        for category,ids in checks.items():
            if ids & set(reservations[category]): raise ValueError(f'{key}: native {category} ID collision')
        for field,cap in [('awakening',8),('synchro',5)]:
            if any(len(t)>cap for t in unit[field]): raise ValueError(f'{key} {field} capacity: {[len(t) for t in unit[field]]}')
        form_label='Custom' if key=='crystal_fina' else str(detail['forms'][form]['rarity'])
        if key!='crystal_fina' and shift: form_label += ' Super Limit Burst' if shift['kind']=='slb' else ' Brave Shift'
        counts={f:{k:sum(g[0]==k for t in unit[f] for g in t) for k in ['ActiveSkill','PassiveSkill']} for f in ['awakening','synchro']}
        awakening_count=sum(counts['awakening'].values())
        mr_count=sum(counts['synchro'].values())
        if not 20<=awakening_count<=28: raise ValueError(f'{key}: awakening count {awakening_count}, expected 20–28')
        presets.append({'id':key,'name':title,'theme':theme,'profile':unit,
                        'balance':{'nativeBudget':budget,'nativeName':native[budget]['name'],'growthDonor':donor,
                                   'activeCount':counts['awakening']['ActiveSkill'],
                                   'passiveCount':counts['awakening']['PassiveSkill'],
                                   'kitCount':awakening_count,
                                   'mrActiveCount':counts['synchro']['ActiveSkill'],
                                   'mrPassiveCount':counts['synchro']['PassiveSkill'],
                                   'mrSkillCount':mr_count,'totalSkillCount':awakening_count+mr_count,
                                   'previousCount':len(actives)+len(passives)-({'reberta':4,'minfilia':1,'lila':1,'trance_terra':4,'primm':1}.get(key,0)),
                                   'additionalPassives':extra_passives+awakening_passives,'playerCopies':additions},
                        'form':{'id':form,'label':form_label,
                                'sha256':None if key=='crystal_fina' else record['sha256'],
                                'source':unit['ffbe']['source']}})
    audit=json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_text())
    missing=[]
    for e in audit['entries']:
        e['assignedTo']=assigned.get((e['kind'],e['id']))
        if not e['assignedTo']: missing.append((e['id'],e['name']))
    if missing: raise ValueError(f'Uncovered grants: {missing}')
    for e in audit['entries']:
        if e['kind']=='ActiveSkill' and e['id']==445210: e['privateClone']='The assigned vision owns the native-equivalent Dual Jobs copy; its mimicableUnitId follows the allocated identity.'
        if e['kind']=='PassiveSkill' and e['id'] in [1406,1410,1411,1418,1420,1432,1433,1454]:
            e['privateClone']='Command/LB condition rebound on a private copy at build time; magnitude, cost and unlock rank retained.'
    audit['status']='All excluded native grants allocated once; owner bindings applied by build helper.'
    (ROOT/'assets/sephira_visions/native_coverage.json').write_text(json.dumps(audit,indent=2)+'\n')
    catalog={'schema':1,'status':'ready','presets':presets,'nativeReservations':reservations,'nativeBudgets':{
        str(vid):{'stats':{k:by_id('Unit/DT_UnitParameter',vid)[k] for k in presets[0]['profile']['stats']},
                  'statRewards':[[rank,*g] for rank,t in enumerate(native[vid]['synchro']) for g in t if g[0]=='BaseParameter']}
        for vid in {p['balance']['nativeBudget'] for p in presets}},
        'grantUnlocks':{f'{kind}:{sid}':[[f,r] for f,r in options] for (kind,sid),options in pool.items()}}
    (ROOT/'assets/sephira_visions/catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    write_visual_policy(catalog)
    describe(catalog, reference)
    print('Generated',len(presets),'presets;',len(assigned),'distinct grants.')


def describe(catalog, reference):
    english=json.loads((reference/'user-animation-reference/inspection/data/ffr_catalog.json').read_text())
    skill={x['id']:x['name'] for x in english['skills']}
    passive={x['id']:x['name'] for x in english['passives']}
    lines=['# Sephira’s Visions','',
        '30 optional, editable presets using the requested FFBE forms. Enable the section on the home page, then build/install. First enable downloads only the missing selected artwork and adds the profiles after all preparations succeed.', '',
        'Turning the section off keeps edits and removed entries; its units and acquisition caves are omitted by the next build. **Restore missing** adds removed presets without resetting existing ones. **Reset all presets** or a card’s **Reset to preset** replaces its kit and appearance, preserves its IDs and acquisition location, and backs up the previous roster in Studio’s character-config backups.', '',
        'An existing custom Crystal Fina is adopted with her current edits and acquisition intact. Reset her explicitly to use this balanced recipe. Other user-added copies and original vision/party edits are preserved.', '',
        '## Balance and coverage', '',
        '- Every preset copies a native level-one stat profile and its exact permanent MR stat rewards/ranks. AP remains the native +8 at MR 4 and +8 at MR 9. Native physical or magic growth curves are used.',
        '- Existing native grants retain their mechanics. Supplemental skills come from the wider native/enemy catalog on private player copies: zero-MP enemy attacks receive MP costs; excessive accuracy, multipliers and hit counts are reduced. Group spells/healing cost more than comparable single-target spells. No FFBE multipliers or FFBE stat conversion are imported. LBs retain one native resonance’s total mechanics; selected elements/damage types follow the requested role.',
        '- All 160 distinct active skills and 131 passives from the 15 excluded original visions are allocated. Within the pack, each exact active/passive appears once; permanent MR stats may repeat. Additional native skills provide thematic attacks and support. Each new vision has its own correctly bound Spirit mastery wrapper.',
        '- Command/LB-specific bonuses use private rebound copies. Native originals remain unchanged. Minfilia’s Dual Jobs selects her own identity. Specific skill bonuses remain grouped with their required attacks.',
        '- Each revised kit has 20–28 awakening abilities/bonuses; learned MR abilities and bonuses are additional. Permanent MR stats, the Spirit wrapper and LB are excluded from both skill counts. Current recipes have 20 awakening grants each, except Elephim with 22. Clive’s Eikon/fire bundle remains together on Reberta. They specialize without being restricted to one action type: healers and debuffers also have attacks. Added visions default to a 1,000-gil vendor price; acquisition can be edited normally.',
        '- Great Dragon is retired from this collection and omitted from builds, including older tagged saved profiles. Reset all presets backs up and removes his old collection entry. His required original grants move to Reberta, Minfilia, Lila, Trance Terra and Primm. Untagged user-created Great Dragons are preserved.',
        '- New enemy copies belong to the vision’s player command; enemy group-toggle partners are disabled so they cannot switch into unbalanced originals. New passives retain native magnitudes/equip costs and required skill dependencies. Revision 3 additions unlock through awakening only; existing MR rewards are unchanged. Boss invulnerability and permanent attack buffs are replaced by finite native player effects; drain restores no more than damage dealt. No new permanent stat boosts are added. Alice’s three earth slams become ice slams with unchanged power/cost.',
        '- Eiko uses the demo’s available Ifrit and Shiva summon commands; their native costs and mechanics are retained. Unreleased espers are not required.', '',
        'The excluded originals are Tronn, Wilhelm, Warrior of Light, Firion, Onion Knight, Cecil, Bartz, Cloud, Squall, Zidane, Tidus, Shantotto, Vaan, Noctis and Clive. Their exact grants, native ranks, descriptions, mechanics and allocations are retained in `assets/sephira_visions/native_coverage.json`.', '',
        '## Kit sizes', '',
        'Revision 3 counts awakening and MR separately and adds 139 awakening grants (135 abilities and 4 bonuses) from the broader catalog. All revision 2 MR rewards are preserved. Existing saved kits are preserved: use **Reset all presets** to apply this revision, then build/install. Individual reset is also available. Reset backs up edits and keeps allocated identity/acquisition.', '',
        '| Vision | Awakening abilities | Awakening bonuses | Awakening total | Additional MR abilities | Additional MR bonuses |',
        '|---|---:|---:|---:|---:|---:|']
    for p in catalog['presets']:
        b=p['balance']; lines.append(f"| {p['name']} | {b['activeCount']} | {b['passiveCount']} | {b['kitCount']} | {b['mrActiveCount']} | {b['mrPassiveCount']} |")
    lines += ['', '## Selected forms and kits', '',
        'Awakening ranks below are numbered 1–4 for readability. MR ranks use the game’s 0–9 values. Native source names are retained for skills so their exact versions remain identifiable.', '']
    for p in catalog['presets']:
        u=p['profile'];lines += [f"### {p['name']} — {p['form']['label']}", '',p['theme']+'.', '',
          f"Sprite `{p['form']['id']}` ({p['form']['source']}); stat/MR budget: {p['balance']['nativeName']}. Growth: {'Terra' if u['donor']==13108 else 'Cloud' if u['donor']==13110 else 'Lightning'}.", '']
        for field,label in [('awakening','Awakening'),('synchro','MR')]:
            for rank,tier in enumerate(u[field]):
                names=[]
                for g in tier:
                    if g[0]=='ActiveSkill': names.append(skill.get(g[1],u['skills'].get(str(g[1]),{}).get('en','Unknown'))+f' [{g[1]}]')
                    if g[0]=='PassiveSkill': names.append(passive[g[1]]+f' [{g[1]}]')
                if names: lines.append(f"- {label} {rank+1 if field=='awakening' else rank}: "+'; '.join(names)+'.')
        lines.append('')
        copies=p['balance']['playerCopies']
        if copies:
            lines += ['Supplemental player copies (native source ID; final MP/power):', '']
            for x in copies:
                s=u['skills'][str(x['id'])]
                # Native power is retained unless explicitly overridden.
                source=next(v for v in english['skills'] if v['id']==x['source'])
                lines.append(f"- {x['name']} ← {x['originalName']} [{x['source']}, {x['sourceCategory']}]: MP {x['adjusted']['Cost']}, power {x['adjusted'].get('magnification',source['mag'])}. {s['desc']}")
            lines.append('')
    lines += ['## Research and validation limits','',
        'Selected hosted packs were checked against their published SHA-256 values, including base packs for shifted forms. Unit records, selected-form sprite motions and LB profiles were inspected. FFBE themes are references, not imported combat numbers. The archived Global datamine is `aEnigmatic/ffbe` at `95727376e82d27acc1290b6dc8ad27ce3c89ea71`; hosted merged records also cover Japanese and post-archive forms. Reberta’s Japanese hosted record has no translated skill list; her requested physical dragoon role and the original Reberta elemental/jump theme guide that kit.', '',
        'Automated checks cover portable configs, unique allocation, native stat/MR budgets, mastery caps, owner-condition rebinding, native table patch serialization, and optional-pack lifecycle. They do not establish live-game balance or prove every animation exists in the demo. Library repairs use the existing unverified-skill controls. The separate **Use borrowed Sephira skill visuals** toggle defaults on; turn it off and rebuild/install to restore the 216 preset source visual mappings without changing mechanics or saved kits. Turn it on and rebuild/install to restore borrowed visuals. Explicit visual donor edits and authored sequences are preserved; missing demo source animations may stay blank.', '',
        '## Full-game release review','',
        'Re-audit native stats, level curves, skill mechanics and unlock ranks; private command/LB conditions and IDs; summon availability; selected form/LB presentation; and vendor/acquisition availability. Preserve user edits and require an explicit reset to apply revised recipes. See README’s running full-release checklist.','']
    (ROOT/'SEPHIRAS_VISIONS.md').write_text('\n'.join(lines))


def write_visual_policy(catalog):
    policy = {'schema': 1, 'presets': {
        p['id']: {str(s['from']): s['visuals'] for s in p['profile']['skills'].values()
                  if s.get('visuals', s['from']) != s['from']}
        for p in catalog['presets']}}
    (ROOT/'assets/existing_visions/payload/sephira_visuals.json').write_text(json.dumps(policy,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reference',type=Path,required=True)
    generate(parser.parse_args().reference)
