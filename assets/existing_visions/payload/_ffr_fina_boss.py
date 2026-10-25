"""Private level-10 Crystal Fina encounter. Never grants or edits a vision."""
import copy
import json
from pathlib import Path

ID = 29670
NAME = 'Studio_CrystalFinaBoss'
UNIT = 'Unit/DT_UnitParameter'
AI = 'Unit/AI/DT_BtlUnitAIParameter'
ASSET = 'Asset/Battle/Unit/DT_BtlUnitAsset'
DESIGN = 'Battle/Unit/DT_BtlUnitDesignParameter'
AI_ASSETS = ('Asset/Battle/AI/DT_BtlUnitAIAsset', 'Asset/Battle/AI/DT_CompositeBtlUnitAIAsset')
DONOR_AI = 'BP/Battle/AI/BossMain/BP_BtlUnitAI_401bellmoder'
PRIVATE_AI = 'BP/Battle/AI/Studio/BP_Studio_CrystalFinaBoss'
SKILLS = 'Skill/DT_SkillData'
FIRST_SKILL = 896700
STATS = {'Level': 10, 'LevelParamId': -1, 'MaxHitPoint': 6500, 'MaxMagicPoint': 500,
         'MaxBreakPoint': 250, 'Attack': 100, 'Defence': 70, 'Intelligence': 105,
         'Mind': 80, 'Agility': 40}


def presentation(units):
    import _ffr_fina_battle as fina
    return fina.selected(units) or {'id': ID, 'jp': NAME,
        'ffbe': {'id': fina.SPRITE, 'source': 'CUSTOM'}}


def recipes():
    data = json.loads(Path(__file__).with_name('crystal_fina_boss.json').read_bytes())
    if data.get('schema') != 1: raise ValueError('Unsupported Crystal Fina boss kit.')
    return [{'source': 0, 'from': 500010, 'visuals': 210250, 'en': 'Attack',
             'set': {'element': 'None', 'magnification': 12}}, *data['skills']]


def skill_ids():
    return {r['source']: FIRST_SKILL + i*10 for i, r in enumerate(recipes())}


def final_rows(rel, expected, units, root):
    """Account for the existing native-body postprocessor in shared tables."""
    if rel in AI_ASSETS:
        if NAME not in expected: return expected
        expected = copy.deepcopy(expected)
        # The row exporter renders hard class imports by object name, whereas
        # the patcher requires a full package/class path to create the import.
        expected[NAME]['UnitAIClass'] = Path(PRIVATE_AI).name + '_C'
        return expected
    if rel not in (ASSET, DESIGN): return expected
    import _ffr_fina_battle as fina
    owner = fina.selected(units, root)
    if owner is None: return expected
    expected = copy.deepcopy(expected)
    matches = [v for v in expected.values() if v.get('ID') == owner['id']]
    if len(matches) != 1: raise ValueError('Missing Fina presentation while verifying boss assets.')
    row, = matches
    if rel == ASSET:
        base = '/Game/' + fina.package(owner, 'FinaNative' + str(owner['id']))
        row['animationAssetList'][0].update(Ss6Project=base, textureBaseColor=base+'_tex',
            textureNormal=base+'_normal', textureMetallicRoughness=base+'_mreo', isVisionCharacter=False,
            Material='/Game/BP/Map/Unit/Material/CharaPBR/M_Ss_Component_PBRBattle')
    else:
        for key, fallback in (('Scale', fina.BATTLE_SPRITE_SCALE), ('attachEffectSacle', 1.0)):
            if float(row[key]) <= 0: row[key] = fallback
    return expected


def prepare(table, rows, units):
    def source(rel, identity):
        found = [(k, v) for k, v in rows(rel).items() if v.get('ID') == identity]
        if len(found) != 1: raise ValueError(f'Crystal Fina boss needs native {rel} ID {identity}.')
        return found[0]
    def add(rel, identity, donor, name, fields):
        if name in rows(rel) or any(v.get('ID') == identity for v in rows(rel).values()) or any(
                v['row'] == name or v['set'].get('ID') == identity for v in table(rel)['add']):
            raise ValueError('Crystal Fina boss identity is occupied: ' + rel + '/' + str(identity))
        key, _ = source(rel, donor)
        table(rel)['add'].append({'row': name, 'cloneFrom': key, 'set': {'ID': identity, **fields}})
    _, donor = source(UNIT, 401)
    if donor.get('Category') != 'Boss' or donor.get('Level') != 4 or donor.get('MaxHitPoint') != 2000:
        raise ValueError('The early boss template changed; Crystal Fina was not built.')
    add(UNIT, ID, 401, NAME, {**STATS, 'Name': 'Crystal Fina',
        'Description': 'Level 10 vision boss test: light magic and measured recovery.',
        'SortId': ID, 'SaveId': ID, 'FaceIconId': 1003, 'Category': 'Boss',
        'Sex': 'Female', 'Race': 'Human', 'IsBoss': True, 'IsAccent': False,
        'ElementResistanceList': {key: ('eResistance::Halved' if key == 'eElement::Light' else
            'eResistance::Weakness' if key == 'eElement::Dark' else 'eResistance::None')
            for key in donor['ElementResistanceList']},
        'HitPoint': 0, 'MagicPoint': 500, 'Breakpoint': 0, 'LimitBurstPoint': 0,
        'passiveSkillList': [], 'WeaponId': -1, 'ArmorId': -1, 'AccessoryIdList': [], 'VisionId': -1,
        'Experience': 0, 'Money': 0, 'DropNormalItem': -1, 'DropNormalItemRate': 0,
        'DropRareItem': -1, 'DropRareItemRate': 0, 'StealNormalItem': -1, 'StealRareItem': -1,
        'StealItemRate': 0, 'BattleVoiceLabel': 'None'})
    owner = presentation(units)
    import _ffr_fina_battle as fina
    # Existing Fina and the boss share the same approved body/runtime. Without
    # an owned vision, the private enemy itself supplies the presentation row.
    base = '/Game/' + fina.package(owner, 'FinaNative' + str(owner['id']))
    add(ASSET, ID, 13108, NAME, {'animationAssetList[0].Ss6Project': base,
        'animationAssetList[0].textureBaseColor': base + '_tex',
        'animationAssetList[0].textureNormal': base + '_normal',
        'animationAssetList[0].textureMetallicRoughness': base + '_mreo',
        'animationAssetList[0].isVisionCharacter': False,
        'animationAssetList[0].Material': '/Game/BP/Map/Unit/Material/CharaPBR/M_Ss_Component_PBRBattle'})
    # The vision inherits its donor's positive scale; BATTLE_SPRITE_SCALE is
    # only a fallback for unset native values, not the normal vision size.
    vision_scale = float(source(DESIGN, 13108)[1]['Scale'])
    if vision_scale <= 0: vision_scale = fina.BATTLE_SPRITE_SCALE
    # Avoid double arithmetic tails (0.9 * 1.3 = 1.1700000000000002).
    # The native FloatProperty row exporter writes the intended scale as 1.17.
    add(DESIGN, ID, 13108, NAME, {'Scale': round(vision_scale * 1.3, 6), 'attachEffectSacle': 1.0,
        'isSpecialDeadAnim': False, 'isFlipH': True})
    ids = skill_ids()
    for i, recipe in enumerate(recipes()):
        identity = FIRST_SKILL + i*10
        fields = {**recipe.get('set', {}), 'SortId': identity, 'Cost': 0, 'hasUnit': 'All',
            'belongCommandList': [912], 'commandIdBelongDebuggingAllSkills': [912, -1],
            'skillIdAfterModeChange': -1, 'isApplyAllMag': False,
            'voiceLabel': 'None', 'selfSkillActivateVoiceLabel': 'None', 'isRemovable': False}
        # Visual variants are cloned alongside their original sound timelines;
        # leave target-side/single/group selection to the game's native router.
        fields.update(playSequencerId=-1, sequencerIdWhenTargetFriendlies=-1)
        if recipe.get('en'): fields['Name'] = recipe['en']
        add(SKILLS, identity, recipe['from'], NAME + '_Skill_' + str(i), fields)
        visual = recipe.get('visuals', recipe['from'])
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
            for offset in (0, 1, 2):
                if any(v.get('ID') == visual + offset for v in rows(rel).values()):
                    add(rel, identity + offset, visual + offset, NAME + '_Visual_' + str(i) + '_' + str(offset), {})
        rel = 'Battle/Sequencer/DT_BtlHitEffectData'
        if any(v.get('ID') == visual for v in rows(rel).values()):
            add(rel, identity, visual, NAME + '_Hit_' + str(i), {})
    add(AI, ID, 401, NAME, {'aiId': ID, 'fightSkillId': ids[0], 'silenceFightId': ids[0],
        'chaseSkillId': -1, 'counterSkillIdList': [-1, -1], 'highRiskSkillIdList': [ids[485203], -1],
        'skillRandData1': [{'SkillId': ids[0], 'Probability': 100.0}],
        'skillRandData2': [{'SkillId': value, 'Probability': 0.0} for value in ids.values()]})
    for rel in AI_ASSETS:
        add(rel, ID, 401, NAME, {'UnitAIClass': '/Game/' + PRIVATE_AI + '.' + Path(PRIVATE_AI).name + '_C'})


def expr(kind, **values):
    return {'$type': 'UAssetAPI.Kismet.Bytecode.Expressions.' + kind + ', UAssetAPI', **values}


def size(node):
    """Unreal's in-memory Kismet offsets (object/property pointers are 8 bytes)."""
    op = node['$type'].split('.')[-1].split(',')[0]
    if op in ('EX_LocalVariable', 'EX_LocalOutVariable', 'EX_InstanceVariable'): return 9
    if op in ('EX_IntConst', 'EX_Jump'): return 5
    if op == 'EX_DoubleConst': return 9
    if op == 'EX_ByteConst': return 2
    if op == 'EX_PrimitiveCast': return 2 + size(node['Target'])
    if op in ('EX_True', 'EX_False', 'EX_EndOfScript', 'EX_Nothing'): return 1
    if op in ('EX_FinalFunction', 'EX_CallMath', 'EX_LocalVirtualFunction'):
        return (14 if op == 'EX_LocalVirtualFunction' else 10) + sum(size(p) for p in node['Parameters'])
    if op == 'EX_Context': return 13 + size(node['ObjectExpression']) + size(node['ContextExpression'])
    if op == 'EX_Let': return 9 + size(node['Variable']) + size(node['Expression'])
    if op in ('EX_LetObj', 'EX_LetBool'): return 1 + size(node['VariableExpression']) + size(node['AssignmentExpression'])
    if op == 'EX_JumpIfNot': return 5 + size(node['BooleanExpression'])
    if op == 'EX_Return': return 1 + size(node['ReturnExpression'])
    raise ValueError('Unsupported boss AI bytecode: ' + op)


def ally_recovery(asset, rotation):
    """Use native friendly-unit HP selection in both think and execute phases.

    The inherited ExecuteInner normally chooses a random target. Its native
    lowest-HP helper instead reads the skill's friendly relation and sets that
    target explicitly, so an injured partner can receive single-target Cure.
    """
    def imported(name):
        return next(-i for i, v in enumerate(asset['Imports'], 1) if v['ObjectName'] == name)
    def add(name, owner, template):
        item = copy.deepcopy(asset['Imports'][-imported(template)-1])
        item.update(ObjectName=name, OuterIndex=imported(owner))
        try: return -(asset['Imports'].index(item)+1)
        except ValueError:
            asset['Imports'].append(item); return -len(asset['Imports'])
    for name in ('CPP_BtlUnit', 'CPP_UnitParameter'): add(name, '/Script/mucha', 'CPP_BtlUnitAI')
    for name, owner in (('GetUnitWithLowestHitPoint', 'CPP_BtlUnitAI'),
                        ('GetScheduledSkill', 'CPP_BtlUnitAI'), ('GetUnitParameter', 'CPP_BtlUnit'),
                        ('GetHitPointRatio', 'CPP_UnitParameter'), ('GreaterEqual_DoubleDouble', 'KismetMathLibrary')):
        add(name, owner, 'GetOwnerUnitParameter')
    def call(name, *args, math=False):
        return expr('EX_CallMath' if math else 'EX_FinalFunction', StackNode=imported(name), Parameters=list(args))
    def context(owner, value):
        return expr('EX_Context', ObjectExpression=owner, Offset=size(value), PropertyType=0,
                    RValuePointer={'$type':'UAssetAPI.Kismet.Bytecode.KismetPropertyPointer, UAssetAPI',
                        'New':{'$type':'UAssetAPI.UnrealTypes.FFieldPath, UAssetAPI', 'Path':[], 'ResolvedOwner':0}},
                    ContextExpression=value)
    # eRelation::Friendlies = 1 in the collected full-game mappings.
    ally = call('GetUnitWithLowestHitPoint', expr('EX_ByteConst', Value=1))
    parameter = context(ally, call('GetUnitParameter'))
    ratio = context(parameter, call('GetHitPointRatio'))
    def condition(threshold):
        return call('GreaterEqual_DoubleDouble', expr('EX_DoubleConst', Value=threshold),
                    expr('EX_PrimitiveCast', ConversionType=4, Target=copy.deepcopy(ratio)), math=True)
    execute = next(e for e in asset['Exports'] if e['ObjectName'] == 'ExecuteInner')
    original = execute['ScriptBytecode']
    if len(original) != 3 or original[0].get('VirtualFunctionName') != 'SetSkillAndTargetWithScheduledSkill':
        raise ValueError('The native boss target-routing function changed.')
    heals = {r['id'] for r in rotation if r.get('healAllies')}
    if len(heals) != 1: raise ValueError('Expected one reviewed friendly recovery skill.')
    test = call('NotEqual_IntInt', call('GetScheduledSkill'), expr('EX_IntConst', Value=next(iter(heals))), math=True)
    branch = expr('EX_JumpIfNot', CodeOffset=0, BooleanExpression=test)
    skip = expr('EX_Jump', CodeOffset=0)
    heal = expr('EX_LocalVirtualFunction', VirtualFunctionName='Set Skill and Lowest Hit Point Target',
                Parameters=[call('GetScheduledSkill')])
    code = [branch, copy.deepcopy(original[0]), skip, heal, *copy.deepcopy(original[1:])]
    branch['CodeOffset'] = sum(map(size, code[:3]))
    skip['CodeOffset'] = sum(map(size, code[:4]))
    execute.update(ScriptBytecode=code, ScriptBytecodeRaw=None, ScriptBytecodeSize=sum(map(size, code)))
    import _ffr_crystal_cave as caves
    caves.names(asset, [asset['Imports'], code])
    return condition


def author_ai(asset, rotation=None):
    """Use the early boss's native think clock and native target routing."""
    asset = copy.deepcopy(asset)
    think, = [e for e in asset['Exports'] if e['ObjectName'] == 'ThinkInner']
    original = think['ScriptBytecode']
    if think['ScriptBytecodeSize'] != 388 or sum(map(size, original)) != 388:
        raise ValueError('The native early-boss AI clock changed.')
    code = copy.deepcopy(original[:3])
    code[2]['Expression']['Parameters'][1] = expr('EX_IntConst', Value=8)
    remainder = copy.deepcopy(original[3]['AssignmentExpression']['Parameters'][0])
    compare = original[3]['AssignmentExpression']['StackNode']
    schedule = next(n['StackNode'] for n in original if n['$type'].split(',')[0].endswith('EX_FinalFunction'))
    ids = skill_ids()
    actions = [(1, ids[210250]), (2, ids[485212]), (3, ids[485230]),
               (5, ids[485215]), (6, ids[210260]), (7, ids[485203])]
    if rotation is not None:
        if len(rotation) != 8 or any(type(r.get('id')) is not int for r in rotation):
            raise ValueError('A vision boss needs eight reviewed actions.')
        actions = [(i, r['id']) for i, r in enumerate(rotation)]
    recovery = ally_recovery(asset, rotation) if rotation and any(r.get('healAllies') for r in rotation) else None
    labels, pending = {}, []
    def jump(label, condition=None):
        n = expr('EX_JumpIfNot', CodeOffset=0, BooleanExpression=condition) if condition else expr('EX_Jump', CodeOffset=0)
        pending.append((n, label)); code.append(n)
    def label(name): labels[name] = sum(map(size, code))
    def cast(identity): code.append(expr('EX_FinalFunction', StackNode=schedule, Parameters=[expr('EX_IntConst', Value=identity)]))
    for turn, _ in actions:
        jump(str(turn), expr('EX_CallMath', StackNode=compare, Parameters=[copy.deepcopy(remainder), expr('EX_IntConst', Value=turn)]))
    label('basic'); cast(rotation[0]['id'] if rotation is not None else ids[0]); jump('end')
    for turn, identity in actions:
        label(str(turn))
        if (rotation[turn]['healing'] if rotation is not None else turn == 5):
            guard = recovery(rotation[turn]['healThreshold']) if recovery and rotation[turn].get('healAllies') else expr('EX_LocalVirtualFunction', VirtualFunctionName='HP判定',
                Parameters=[expr('EX_DoubleConst', Value=rotation[turn].get('healThreshold', .5)
                                 if rotation is not None else .5), expr('EX_True')])
            jump('basic', guard)
        cast(identity); jump('end')
    label('end'); code.extend(copy.deepcopy(original[-2:]))
    for n, target in pending: n['CodeOffset'] = labels[target]
    think.update(ScriptBytecode=code, ScriptBytecodeRaw=None, ScriptBytecodeSize=sum(map(size, code)))
    # Preserve every original loaded property and object dependency. New names
    # must remain in IoStore's referenced prefix, just as with the choice menu.
    for name in ('HP判定',):
        if name not in asset['NameMap']: asset['NameMap'].append(name)
    asset['NamesReferencedFromExportDataCount'] = len(asset['NameMap'])
    return asset


def build(env):
    legacy, out, root = (Path(env[k]) for k in ('LEGACY', 'OUT', 'ROOT'))
    source = legacy / ('FFRS/Content/' + DONOR_AI + '.uasset')
    if not source.is_file():
        env['run'](env['ffrenv'].py(str(root/'tools/extract_legacy.py'), '--filter', DONOR_AI))
    if not source.is_file(): raise ValueError('The early-boss AI package is unavailable.')
    work = Path(env['BUILD'])/'crystal-fina-boss'; work.mkdir(parents=True, exist_ok=True)
    patch = work/'clone.json'
    patch.write_text(json.dumps({'legacyRoot': str(legacy), 'outRoot': str(out), 'clones': [{
        'from': 'FFRS/Content/' + DONOR_AI, 'to': 'FFRS/Content/' + PRIVATE_AI,
        'rename': [[Path(DONOR_AI).name, Path(PRIVATE_AI).name]]}]}), encoding='utf-8')
    env['run']([*env['FFRDT'], 'patch', str(patch), '--usmap', env['USMAP']])
    target = out/('FFRS/Content/' + PRIVATE_AI + '.uasset'); dump = work/'ai.json'
    env['run']([*env['FFRDT'], 'tojson', str(target), str(dump), '--usmap', env['USMAP']])
    authored = author_ai(json.loads(dump.read_text(encoding='utf-8-sig')))
    dump.write_text(json.dumps(authored, ensure_ascii=False), encoding='utf-8')
    env['run']([*env['FFRDT'], 'fromjson', str(dump), str(target), '--usmap', env['USMAP']])
    env['run']([*env['FFRDT'], 'tojson', str(target), str(dump), '--usmap', env['USMAP']])
    built = json.loads(dump.read_text(encoding='utf-8-sig'))
    for field in ('ScriptBytecode', 'ScriptBytecodeSize'):
        original = next(e[field] for e in authored['Exports'] if e['ObjectName'] == 'ThinkInner')
        result = next(e[field] for e in built['Exports'] if e['ObjectName'] == 'ThinkInner')
        if result != original: raise ValueError('Crystal Fina boss AI failed native serialization: ' + field)
    print('  Crystal Fina boss: level 10, 6,500 HP; eight-action light-magic rotation, bounded recovery; no vision reward.')
