import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from audit_ability_animations import DecoderCache, audit_catalog, write_report


class AnimationAuditTests(unittest.TestCase):
    def test_audit_collects_every_failure_and_keeps_unmapped_and_native_entries(self):
        skills = [{'id': i, 'name': f'Skill {i}', 'attr': 'Ability', 'hits': 1,
                   'seq': [1] if i == 4 else []} for i in range(1, 6)]
        policy = {str(i): {'donor': 99, 'donorName': 'Donor', 'rule': 'test', 'tier': 1} for i in range(1, 4)}
        def target(sid):
            if sid != 1: raise ValueError('missing ' + str(sid))
            return {'events': [{'set': {'EventType': 'EffectSpawnNiagaraAtTarget'}}]}
        report = audit_catalog(SimpleNamespace(catalog={'skills': skills}, visual_policy=policy, target_effects=target))
        self.assertEqual(report['summary'], {'audited_target_effects': 1, 'effect_error': 2,
                                            'native_sequence_retained': 1, 'motion_only_fallback': 1})
        self.assertFalse(report['inGameValidated'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'report'; write_report(report, path)
            self.assertEqual(json.loads(path.with_suffix('.json').read_text()), report)
            self.assertIn('missing 3', path.with_suffix('.csv').read_text(encoding='utf-8-sig'))

    def test_decode_cache_changes_when_either_source_mapping_or_decoder_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); asset = root/'sample.uasset'; payload = root/'sample.uexp'
            mapping = root/'Mappings.usmap'; decoder = root/'decoder.exe'
            for p in (asset, payload, mapping, decoder): p.write_bytes(b'initial')
            def key(): return DecoderCache([str(decoder)], mapping, root/'cache').paths(asset)
            previous = key()
            for p in (asset, payload, mapping, decoder):
                p.write_bytes(b'changed'); updated = key()
                self.assertNotEqual(updated, previous); previous = updated


if __name__ == '__main__': unittest.main()
