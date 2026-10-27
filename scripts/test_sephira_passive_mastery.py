"""Collection-wide coverage, passive placement and elemental icon contracts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_existing_visions import ROOT, native
from test_sephira_runtime_rewards import inputs
import _ffr_sephira as pack
from sephira_passive_mastery import REWARDS


class PassiveMasteryTests(unittest.TestCase):
    def test_original_passives_and_approved_replacement_keep_150_transferable_mr_slots(self):
        catalog, _, units = inputs()
        audit = json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
        required = {e['id'] for e in audit['entries'] if e['kind'] == 'PassiveSkill'}
        actual = []; learned = set()
        for preset, unit in zip(catalog['presets'], units):
            ranks=(2,3,5,7,9) if preset['id']=='mystea' else (1,3,5,7,9)
            choices = [unit['synchro'][rank][0] for rank in ranks]
            self.assertTrue(all(g[0] in ('ActiveSkill','PassiveSkill') for g in choices))
            expected = list(REWARDS[preset['id']])
            for rank, bound, general, _ in pack.MASTERY_SCOPE.get(preset['id'], []):
                expected[(rank-1)//2] = general
            if preset['id']=='aria':expected[-1]=1524
            if preset.get('mrRestoration'):
                update=preset['mrRestoration']
                for step in update.get('steps',[update]):
                    for op in step['mr']:expected[(op['rank']-1)//2]=op['to'][1]
            for op in preset.get('kitUpdate',{}).get('mr',[]):
                if op['rank'] in ranks:expected[ranks.index(op['rank'])]=op['to'][1]
            self.assertEqual([g[1] for g in choices], expected)
            self.assertFalse({g[1] for g in choices} & pack.BINDINGS.keys())
            learned.update(g[1] for f in ('awakening','synchro') for t in unit[f]
                           for g in t if g[0]=='PassiveSkill')
            actual.extend(g[1] for g in choices)
            previous = {g[1] for field in ('awakening','synchro')
                        for tier in preset['revision5Progression'][field] for g in tier if g[0]=='ActiveSkill'}
            if not preset.get('kitUpdate') and not preset.get('mrRestoration'):
                self.assertEqual({g[1] for tier in unit['awakening'] for g in tier if g[0]=='ActiveSkill'}, previous)
        self.assertEqual(len(required), 131)
        self.assertEqual(len(actual), 150)
        # The user explicitly replaced Vaan-only One for the Road with
        # Pharmacology. Keep the collected original audit intact.
        self.assertEqual(required - learned, {1435})
        self.assertIn(1044, learned)

    def test_scope_repair_preserves_complete_kits_and_old_private_reward_ids(self):
        catalog, rows, units = inputs()
        for preset, unit in zip(catalog['presets'],units):
            update=preset.get('masteryScopeUpdate')
            if not update:continue
            old=copy.deepcopy(unit);old.update(copy.deepcopy(update['before']))
            expected={g[1] for f in ('awakening','synchro') for t in old[f] for g in t if g[0]=='PassiveSkill'}
            fixed=copy.deepcopy(old);pack.repair_mastery_scope(fixed)
            self.assertEqual({g[1] for f in ('awakening','synchro') for t in fixed[f] for g in t if g[0]=='PassiveSkill'},expected)
            scope_target=preset.get('mrRestoration',{}).get('before',unit)
            for f in ('awakening','synchro'):self.assertEqual(fixed[f],scope_target[f])
            pack.repair_mastery_scope(fixed)
            for f in ('awakening','synchro'):self.assertEqual(fixed[f],scope_target[f])
            bound=pack.bind_units([old],rows.__getitem__)[0]
            mr={g[1] for t in bound['synchro'] for g in t if g[0]=='PassiveSkill'}
            for _,sid,_,_ in pack.MASTERY_SCOPE[preset['id']]:
                self.assertNotIn(pack.private_passive_id(preset['id'],sid),mr)
            if preset['id']=='christine':
                trait=next(b for b in bound['_sephiraBindings'] if b['passive']['set']['ID']==pack.private_passive_id('christine',1406))
                self.assertEqual(trait['effect']['set']['ParamList'][1],unit['command']['id'])
                self.assertIn('Christine',trait['passive']['set']['Description'])
                self.assertNotIn('Tronn',trait['passive']['set']['Description'])
            for sid in (1418,1433):
                extra=pack.SIGNATURE_BINDINGS.get((preset['id'],sid),[])
                if not extra:continue
                trait=next(b for b in bound['_sephiraBindings'] if b['passive']['set']['ID']==pack.private_passive_id(preset['id'],sid))
                for slot,native_id,source in extra:
                    target=next(int(k) for k,r in unit['skills'].items() if r['from']==source)
                    self.assertEqual(trait['effect']['set']['ParamList'][slot],target)

    def test_complete_passive_kits_match_native_budgets_without_duplicate_stat_tiers(self):
        catalog, rows, units = inputs()
        reference = json.loads((ROOT/'scripts/fixtures/sephira_awakening_budgets.json').read_bytes())
        stat_tiers = [(1273,1309), (1275,1311,1310), (1378,1379), (1380,1381),
                      (1316,1277,1317), (1312,1313,1274), (1314,1315,1276),
                      (1279,1376), (1283,1375), (1321,1247)]
        for preset, unit in zip(catalog['presets'],units):
            original = reference[str(preset['balance']['nativeBudget'])]
            ids = [g[1] for field in ('awakening','synchro') for tier in unit[field]
                   for g in tier if g[0]=='PassiveSkill']
            self.assertEqual(len(ids),len(set(ids)),unit['key'])
            from sephira_mr_layout import PASSIVE_DELTAS
            delta=PASSIVE_DELTAS.get(preset['id'],0)
            self.assertEqual(len(ids),len(original['passives'])+delta,unit['key'])
            self.assertEqual(preset['awakeningBalance'].get('requestedPassiveDelta',0),delta)
            self.assertEqual(preset['awakeningBalance']['nativePassives'],original['passives'])
            mastery = {g[1] for tier in unit['synchro'] for g in tier if g[0]=='PassiveSkill'}
            for group in stat_tiers:
                # Mog already preserves two native Speed rewards in MR. The
                # additive pass must not create another stacked stat tier.
                self.assertLessEqual(len(set(ids)&set(group)),max(1,len(mastery&set(group))),
                                     (unit['key'],group))
            self.assertTrue(all(len(t)<=8 for t in unit['awakening']))
            native_passives = {p['ID']:p for p in rows[pack.PASSIVE].values()}
            from sephira_esper_kits import PASSIVES
            native_passives.update({sid:{'equipCost':p['cost']} for sid,p in PASSIVES.items()})
            cost = sum(native_passives[s]['equipCost'] or 20 for s in ids)
            self.assertTrue(.8*original['cost'] <= cost <= 1.2*original['cost'],unit['key'])
        tronn = next(p for p in catalog['presets'] if p['id']=='christine')['profile']
        self.assertEqual(sum(g[0]!='ActiveSkill' for f in ('awakening','synchro')
                             for tier in tronn[f] for g in tier),16)

    def test_all_elemental_damage_icons_match_damage_with_explicit_user_overrides_preserved(self):
        _, rows, units = inputs()
        for unit in units:
            for recipe in unit['skills'].values(): recipe['set'].pop('SkillIcon.TagName', None)
        before = copy.deepcopy(units)
        native_skills = {s['ID']:s for s in rows['Skill/DT_SkillData'].values()}
        fixed = 0
        for unit in pack.player_units(units, rows.__getitem__):
            for recipe in unit['skills'].values():
                source = native_skills[recipe['from']]; effective = dict(source, **recipe['set'])
                if (effective.get('skillEffectType') == 'DamageAndRecovery' and
                    effective.get('parameterVariationType') == 'Decrease' and effective.get('parameterType') == 'HitPoint' and
                    effective.get('element') in ('Fire','Ice','Thunder','Water','Wind','Earth','Light','Dark')):
                    self.assertEqual(recipe['set']['SkillIcon.TagName'], 'UI.Skill.Action.Icon.' + effective['element'])
                    fixed += source['SkillIcon']['TagName'] != recipe['set']['SkillIcon.TagName']
        self.assertEqual(fixed, 39)
        self.assertEqual(units, before)
        recipe = next(r for u in units for r in u['skills'].values() if r['set'].get('element')=='Ice')
        recipe['set']['SkillIcon.TagName'] = 'UI.Skill.Action.Icon.Support'
        result = pack.player_units(units, rows.__getitem__)
        changed = next(r for u in result for r in u['skills'].values() if r['jp']==recipe['jp'])
        self.assertEqual(changed['set']['SkillIcon.TagName'], 'UI.Skill.Action.Icon.Support')

    def test_more_than_16_command_icons_have_distinct_brushes_and_keep_original_icons(self):
        catalog, _, units = inputs()
        original = {'original': {'Tag': {'TagName':'UI.Skill.Command.Icon.13110'},
                                 'Brush': {'ResourceObject':'Cloud'}}}
        tables = {}
        for unit in units:
            native.prepare_command_icon(tables, unit, lambda _: original)
        for rel, plan in tables.items():
            self.assertEqual(plan['set'], [])
            self.assertEqual(len(plan['add']), 30)
            tags = set()
            for unit, op in zip(units, plan['add']):
                fields = op['set']; tags.add(fields['Tag.TagName'])
                self.assertEqual(fields['Tag.TagName'], native.command_icon(unit, units, [], None))
                self.assertEqual(fields['Brush.ResourceObject'],
                                 f'/Game/UI/Textures/Icon/menu/ICON_Ability_summon{unit["id"]}')
            self.assertEqual(len(tags), 30)
        self.assertEqual(original['original']['Brush']['ResourceObject'], 'Cloud')


if __name__ == '__main__': unittest.main()
