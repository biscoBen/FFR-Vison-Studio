"""Original MR utility must remain transferable at its native story/rank gate."""
import copy
import json
from pathlib import Path
import unittest
from test_sephira_runtime_rewards import inputs
import _ffr_sephira as pack
from audit_sephira_mr import audit

ROOT=Path(__file__).resolve().parents[1]


class MrRestorationTests(unittest.TestCase):
    def test_all_75_original_rewards_are_mr_and_restored_actives_keep_gates_ranks_and_native_commands(self):
        catalog,rows,units=inputs();source=json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
        result=audit(catalog,source)
        self.assertEqual(result['summary']['covered_mr'],75)
        self.assertFalse(any(result['summary'][s] for s in ('awakening_only','missing_from_learned_kits','mr_copy_needs_review')))
        plan=json.loads((ROOT/'scripts/fixtures/sephira_mr_restoration_plan.json').read_bytes())
        by={p['id']:p for p in catalog['presets']};original={r['id']:r for r in result['rewards']}
        origin_ids={v['name']:v['id'] for v in source['excludedVisions']}
        native={r['ID']:r for r in rows['Skill/DT_SkillData'].values()}
        for key,rank,identity in plan['placements']:
            self.assertEqual(by[key]['profile']['synchro'][rank][0],['ActiveSkill',identity,-1])
            old=original[identity]['originalMr'][0]
            self.assertEqual(rank,old['rank'])
            self.assertEqual(by[key]['profile']['studioAcquisition']['location'],'sephira_'+str(origin_ids[old['vision']]))
            self.assertEqual(native[identity]['belongCommandList'],[1])
            self.assertGreaterEqual(native[identity]['equipCost'],0)
        for key in ('crystal_fina','aria'):self.assertNotIn('mrRestoration',by[key])

    def test_old_rosters_receive_only_the_declared_progression_changes_once(self):
        catalog,_,_=inputs()
        for preset in catalog['presets']:
            op=preset.get('mrRestoration')
            if not op:continue
            unit=copy.deepcopy(preset['profile']);unit.update(copy.deepcopy(op['before']));unit.pop('sephiraMrRevision',None)
            unit[pack.FIELD]={'version':1,'preset':preset['id'],'enabled':True}
            before=copy.deepcopy(unit)
            pack.repair_equipable_mr(unit)
            for f in ('awakening','synchro'):
                self.assertEqual([sorted(map(tuple,t)) for t in unit[f]],
                                 [sorted(map(tuple,t)) for t in preset['profile'][f]],preset['id'])
            for f in before.keys()-{'awakening','synchro'}:self.assertEqual(unit[f],before[f],(preset['id'],f))
            self.assertEqual(unit['master']['id'],before['master']['id'])
            again=copy.deepcopy(unit);pack.repair_equipable_mr(unit);self.assertEqual(unit,again)
        # A deliberate MR edit is reported before the build starts converting.
        preset=next(p for p in catalog['presets'] if p['id']=='christine')
        unit=copy.deepcopy(preset['profile']);unit.update(copy.deepcopy(preset['mrRestoration']['before']));unit.pop('sephiraMrRevision')
        unit[pack.FIELD]={'version':1,'preset':'christine','enabled':True};unit['synchro'][5][0]=['PassiveSkill',1009,-1]
        with self.assertRaisesRegex(ValueError,'MR5 was edited'):pack.repair_equipable_mr(unit)


if __name__=='__main__':unittest.main()
