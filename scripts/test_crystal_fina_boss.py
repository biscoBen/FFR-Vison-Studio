"""Exercise the private boss recipe and execute its actual Kismet rotation."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'assets/existing_visions/payload'))
import _ffr_fina_boss as boss
import _ffr_fina_battle as battle
import _ffr_testing as testing

FIXTURE = ROOT/'scripts/fixtures/crystal_fina_boss'


def native_ai(): return json.loads(gzip.decompress((FIXTURE/'ai.json.gz').read_bytes()))


def choose(asset, turn, hp):
    """Small interpreter for the native instructions authored for this boss.

    Unlike a parallel Python rotation, this follows the serialized jump offsets,
    locals and native calls that Unreal receives. Every turn must schedule once.
    """
    code = next(e['ScriptBytecode'] for e in asset['Exports'] if e['ObjectName'] == 'ThinkInner')
    positions, offset = {}, 0
    for node in code:
        positions[offset] = node; offset += boss.size(node)
    locals_, scheduled = {}, []
    def path(node): return tuple(node['Variable']['New']['Path'])
    def op(node): return node['$type'].split('.')[-1].split(',')[0]
    def evaluate(node):
        kind = op(node)
        if kind in ('EX_IntConst', 'EX_DoubleConst'): return node['Value']
        if kind == 'EX_True': return True
        if kind in ('EX_LocalVariable', 'EX_LocalOutVariable'): return locals_.get(path(node), False)
        if kind in ('EX_FinalFunction', 'EX_CallMath'):
            name = asset['Imports'][-node['StackNode']-1]['ObjectName']
            args = [evaluate(p) for p in node['Parameters']]
            if name == 'GetOwnerUnitParameter': return 'owner'
            if name == 'GetThinkNum': return turn
            if name == 'Percent_IntInt': return args[0] % args[1]
            if name == 'NotEqual_IntInt': return args[0] != args[1]
            if name == 'SetScheduledSkill': scheduled.append(args[0]); return None
            raise AssertionError(name)
        if kind == 'EX_LocalVirtualFunction':
            assert node['VirtualFunctionName'] == 'HP判定'
            threshold, below = [evaluate(p) for p in node['Parameters']]
            assert below is True
            return hp <= threshold
        if kind == 'EX_Context': return evaluate(node['ContextExpression'])
        raise AssertionError(kind)
    pc = 0
    for _ in range(100):
        node = positions[pc]; kind = op(node); next_pc = pc + boss.size(node)
        if kind == 'EX_LetObj': locals_[path(node['VariableExpression'])] = evaluate(node['AssignmentExpression'])
        elif kind == 'EX_Let': locals_[path(node['Variable'])] = evaluate(node['Expression'])
        elif kind == 'EX_Jump': next_pc = node['CodeOffset']
        elif kind == 'EX_JumpIfNot':
            if not evaluate(node['BooleanExpression']): next_pc = node['CodeOffset']
        elif kind == 'EX_Return':
            assert len(scheduled) == 1, scheduled
            return scheduled[0]
        else: evaluate(node)
        pc = next_pc
    raise AssertionError('AI did not finish')


class CrystalFinaBossTests(unittest.TestCase):
    def test_every_turn_schedules_a_valid_action_and_healing_is_bounded(self):
        source = native_ai(); before = copy.deepcopy(source); asset = boss.author_ai(source)
        ids = boss.skill_ids()
        normal = [ids[0], ids[210250], ids[485212], ids[485230], ids[0], ids[0], ids[210260], ids[485203]]
        low = normal[:]; low[5] = ids[485215]
        for turn in range(80):
            self.assertEqual(choose(asset, turn, 1), normal[turn%8])
            self.assertEqual(choose(asset, turn, .49), low[turn%8])
        self.assertEqual(choose(asset, 5, .5), ids[485215])
        self.assertEqual(choose(asset, 5, .501), ids[0])
        self.assertEqual(source, before)
        # Revival/Reraise and full-strength Curaga never enter the solo rotation.
        self.assertFalse({ids[210150],ids[485206],ids[485209]} & set(low))
        self.assertIn('HP判定', asset['NameMap'][:asset['NamesReferencedFromExportDataCount']])
        broken = copy.deepcopy(asset)
        code = next(e['ScriptBytecode'] for e in broken['Exports'] if e['ObjectName'] == 'ThinkInner')
        next(n for n in code if 'CodeOffset' in n)['CodeOffset'] = 3
        with self.assertRaises(KeyError): choose(broken, 1, 1)

    def test_boss_is_self_contained_with_no_grants_or_native_row_edits(self):
        source = json.loads(gzip.decompress((FIXTURE/'rows.json.gz').read_bytes()))
        before = copy.deepcopy(source); operations = {}
        def table(rel): return operations.setdefault(rel, {'add': [], 'set': []})
        boss.prepare(table, lambda rel: source[rel], [])
        built = copy.deepcopy(source)
        for rel, plan in operations.items():
            self.assertFalse(plan['set'])
            for edit in plan['add']:
                built[rel][edit['row']] = testing.apply_fields(source[rel][edit['cloneFrom']], edit['set'])
            for key, row in source[rel].items(): self.assertEqual(built[rel][key], row)
        row = built[boss.UNIT][boss.NAME]
        self.assertEqual(row['Category'], 'Boss'); self.assertEqual(row['LevelParamId'], -1)
        self.assertEqual(row['MaxHitPoint'], 6500); self.assertFalse(row['passiveSkillList'])
        self.assertEqual(row['ElementResistanceList']['eElement::Fire'], 'eResistance::None')
        self.assertEqual(row['ElementResistanceList']['eElement::Thunder'], 'eResistance::None')
        self.assertEqual(row['ElementResistanceList']['eElement::Light'], 'eResistance::Halved')
        self.assertEqual(row['ElementResistanceList']['eElement::Dark'], 'eResistance::Weakness')
        self.assertEqual(row['Experience']+row['Money'],0); self.assertEqual(row['DropNormalItem'], -1)
        self.assertEqual(source, before)
        # This separate level-10 practice boss keeps its tested rotation and
        # bounded healing; player kit edits must not silently retune it.
        preset = json.loads((ROOT/'scripts/fixtures/sephira_user_kits_before.json').read_bytes())['crystal_fina']
        abilities = {g[1] for tier in preset['awakening'] for g in tier if g[0]=='ActiveSkill'}
        self.assertEqual(set(boss.skill_ids()), abilities | {0})
        ray = next(v for v in built[boss.SKILLS].values() if v['ID'] == boss.skill_ids()[485212])
        self.assertEqual(ray['magnification'],32); self.assertEqual(ray['Cost'],0)
        self.assertEqual(ray['defaultTargetRelation'],'Enemies')
        heal = next(v for v in built[boss.SKILLS].values() if v['ID'] == boss.skill_ids()[485215])
        self.assertEqual(heal['magnification'],20); self.assertEqual(heal['defaultTargetRelation'],'Friendlies')
        self.assertNotIn('Item/Vision/DT_VisionItemData', operations)
        self.assertNotIn(testing.COMMON, operations)
        self.assertTrue(built[boss.DESIGN][boss.NAME]['isFlipH'])
        self.assertEqual(built[boss.DESIGN][boss.NAME]['Scale'], 1.17)
        with tempfile.TemporaryDirectory() as root:
            settings = Path(root)/testing.CONFIG; settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({'schema':1,'maxMr':False,'practiceBattle':True}))
            owner = battle.selected([], root); self.assertEqual(owner['id'], boss.ID)
            self.assertEqual(boss.final_rows(boss.ASSET, built[boss.ASSET], [], root), built[boss.ASSET])
            settings.write_text(json.dumps({'schema':1,'maxMr':False}))
            self.assertIsNone(battle.selected([], root))
        source[boss.UNIT]['collision'] = {'ID':boss.ID}
        with self.assertRaisesRegex(ValueError, 'occupied'): boss.prepare(table, lambda rel: source[rel], [])

    def test_owned_vision_presentation_is_shared_but_its_kit_is_independent(self):
        unit = {'id':13503, 'jp':'My Fina', 'ffbe':{'id':battle.SPRITE,'source':'CUSTOM'},
                'stats': {'MaxHitPoint':99999}, 'skills':{'custom':{'from':210190}}}
        source = json.loads(gzip.decompress((FIXTURE/'rows.json.gz').read_bytes())); operations = {}
        boss.prepare(lambda rel: operations.setdefault(rel,{'add':[],'set':[]}),lambda rel: source[rel],[unit])
        asset, = operations[boss.ASSET]['add']
        self.assertIn('/13503/FinaNative13503',asset['set']['animationAssetList[0].Ss6Project'])
        self.assertEqual(operations[boss.UNIT]['add'][0]['set']['MaxHitPoint'],6500)
        self.assertEqual(operations[boss.DESIGN]['add'][0]['set']['Scale'],1.17)

    def test_verification_combines_owned_fina_postprocessing_without_exempting_other_rows(self):
        unit = {'id':13503, 'jp':'My Fina', 'ffbe':{'id':battle.SPRITE,'source':'CUSTOM'}}
        original = json.loads(gzip.decompress((FIXTURE/'rows.json.gz').read_bytes()))[boss.ASSET]
        key = next(k for k,v in original.items() if v['ID'] == 13108)
        operation = {'add':[], 'set':[]}
        plan = {'add':[{'row':'My Fina', 'cloneFrom':key, 'set':{'ID':13503}}], 'set':[]}
        expected = copy.deepcopy(original)
        expected['My Fina'] = testing.apply_fields(original[key],{'ID':13503})
        with tempfile.TemporaryDirectory() as root:
            final = lambda rows: boss.final_rows(boss.ASSET,rows,[unit],root)
            built = final(expected)
            testing.check_rows(original,built,operation,plan,final)
            self.assertEqual(built[key],original[key])
            built[key]['shadowScale'] = 99
            with self.assertRaises(ValueError): testing.check_rows(original,built,operation,plan,final)


if __name__ == '__main__': unittest.main()
