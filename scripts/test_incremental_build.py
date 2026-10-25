"""Reuse must survive setting-only edits without keeping removed/corrupt assets."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/existing_visions/payload'))
from _ffr_build_cache import Cache,sprite_targets
import _ffr_build_cache as reuse


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'build/assets'
        self.source=self.root/'units/unit.csv';self.source.parent.mkdir();self.source.write_bytes(b'original')
        self.targets=[self.out/'example.uasset'];self.calls=0

    def action(self):
        self.calls+=1;self.out.mkdir(parents=True,exist_ok=True)
        self.targets[0].write_bytes(b'asset'+self.source.read_bytes())
        self.targets[0].with_suffix('.uexp').write_bytes(b'export')

    def run_stage(self,cache=None,value=None):
        return (cache or Cache(self.root,{'game':'one','code':'one'})).execute(
            'sprites',value or {'id':13501},[self.source],self.targets,self.action)

    def test_warm_build_restores_verified_output_into_fresh_folder(self):
        self.assertFalse(self.run_stage());expected=self.targets[0].read_bytes()
        shutil.rmtree(self.out)
        self.assertTrue(self.run_stage());self.assertEqual(self.calls,1)
        self.assertEqual(self.targets[0].read_bytes(),expected)
        # Editing restored output must not mutate cache via a shared hard link.
        self.targets[0].write_bytes(b'later timeline edit')
        self.assertTrue(self.run_stage());self.assertEqual(self.targets[0].read_bytes(),expected)

    def test_changed_source_game_or_converter_regenerates_only_affected_stage(self):
        self.run_stage();self.source.write_bytes(b'modified');self.assertFalse(self.run_stage())
        self.assertFalse(self.run_stage(Cache(self.root,{'game':'two','code':'one'})))
        self.assertFalse(self.run_stage(Cache(self.root,{'game':'two','code':'two'})))
        self.assertEqual(self.calls,4)

    def test_cached_fina_movie_keeps_its_soundtrack_and_invalidates_changed_audio(self):
        import _ffr_incremental as inc
        import _ffr_fina_cinematic as film
        import _ffr_fina_cave_music as music
        legacy=self.root/'legacy';mapping=self.root/'mapping.usmap';mapping.write_bytes(b'mapping')
        tools=self.root/'tools';tools.mkdir()
        for name in ('fina_cinematic.zip','cave_music_preview.zip'):(tools/name).write_bytes(b'payload')
        asset='FFRS/Content/Sequencer/Battle/Skill/444010/444011/SEQ_Battle_444011_Master'
        master=self.out/(asset+'.uasset');master.parent.mkdir(parents=True);master.write_bytes(b'original')
        master.with_suffix('.uexp').write_bytes(b'original export')
        score=self.root/'scored.usm';score.write_bytes(b'picture and audio')
        env={'ROOT':self.root,'LEGACY':legacy,'OUT':self.out,'USMAP':mapping,'lb_id':lambda _:444010,
             'authored_sequences':[{'asset':asset,'plan':{'duration':400000}}],
             'run':lambda _:None,'ffrenv':SimpleNamespace()}
        calls=[]
        def generate(units,env):
            calls.append(True)
            paths=[master,*[master.parent/'Track'/f'SEQ_Battle_444011_{s}.uasset'
                            for s in ('Cut_000','Sound_001','Effect_000')],
                   *[self.out/(film.PRIVATE+s+'.uasset') for s in ('','_vp9')]]
            for path in paths:
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(score.read_bytes())
                path.with_suffix('.uexp').write_bytes(b'export')
            timeline=self.root/'build/fina-cinematic/timeline.json'
            timeline.parent.mkdir(parents=True,exist_ok=True);timeline.write_text('{}')
        with mock.patch.object(film,'enabled',return_value=True),mock.patch.object(film,'matches',return_value=True),mock.patch.object(
                music,'movie_audio',return_value=score),mock.patch.object(inc,'_ensure_native'),mock.patch.object(film,'prepare_pak') as pak,mock.patch.object(
                reuse,'_active',Cache(self.root,{})),mock.patch.dict(sys.modules,{'ffbe_resonance':SimpleNamespace(SHELL='shell',__file__=str(self.source))}):
            wrapped=inc._cinematic(generate)
            wrapped([{'id':13500}],env)
            master.write_bytes(b'original');master.with_suffix('.uexp').write_bytes(b'original export')
            wrapped([{'id':13500}],env)
            self.assertEqual(len(calls),1)
            self.assertEqual(pak.call_args.args[-1],score.read_bytes())
            score.write_bytes(b'new audio with same pictures')
            master.write_bytes(b'original');master.with_suffix('.uexp').write_bytes(b'original export')
            wrapped([{'id':13500}],env)
            self.assertEqual(len(calls),2)

    def test_corruption_and_incomplete_manifest_trigger_regeneration(self):
        self.run_stage();folder=next((self.root/'build/reuse').glob('*/*'))
        (folder/'0.bin').write_bytes(b'broken');self.assertFalse(self.run_stage())
        (folder/'manifest.json').write_text('{}');self.assertFalse(self.run_stage())
        self.assertEqual(self.calls,3)

    def test_failed_generation_is_not_reused(self):
        c=Cache(self.root,{})
        def fail():raise RuntimeError('failed')
        with self.assertRaisesRegex(RuntimeError,'failed'):c.execute('sprites',{},[self.source],self.targets,fail)
        self.assertFalse(list((self.root/'build/reuse').glob('*/*/manifest.json')))

    def test_in_place_asset_transform_keys_original_and_retains_optional_sidecar_state(self):
        self.action();c=Cache(self.root,{})
        def transform():self.targets[0].with_suffix('.uexp').write_bytes(b'changed')
        self.assertFalse(c.execute('timeline',{},self.targets,self.targets,transform))
        self.action();self.targets[0].with_suffix('.ubulk').write_bytes(b'stale')
        # Sidecars are inputs, so a changed input bulk must miss first.
        self.assertFalse(c.execute('timeline',{},self.targets,self.targets,transform))
        self.action();self.targets[0].with_suffix('.ubulk').unlink()
        self.assertTrue(c.execute('timeline',{},self.targets,self.targets,lambda:self.fail('must reuse')))
        self.assertFalse(self.targets[0].with_suffix('.ubulk').exists())
        self.assertEqual(self.targets[0].with_suffix('.uexp').read_bytes(),b'changed')

    def test_input_change_during_generation_prevents_cache_commit(self):
        def mutate():self.action();self.source.write_bytes(b'changed during build')
        with self.assertRaisesRegex(ValueError,'changed during generation'):
            Cache(self.root,{}).execute('sprite',{},[self.source],self.targets,mutate)
        self.assertFalse(list((self.root/'build/reuse').glob('*/*/manifest.json')))

    def test_cached_asset_for_removed_unit_is_not_restored(self):
        c=Cache(self.root,{})
        targets=[]
        for uid in (13500,13501):
            selected=sprite_targets(self.out,uid);targets.append(selected)
            def build(paths=selected):
                for p in paths:
                    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'asset');p.with_suffix('.uexp').write_bytes(b'export')
            c.execute('sprites',uid,[self.source],selected,build)
        shutil.rmtree(self.out)
        c.execute('sprites',13500,[self.source],targets[0],lambda:self.fail('unchanged unit'))
        self.assertFalse(any('13501' in str(p) for p in self.out.rglob('*')))

    def test_map_package_reuses_export_and_bulk_sidecars_together(self):
        self.targets=[self.out/'map.umap']
        self.assertFalse(self.run_stage())
        shutil.rmtree(self.out)
        self.assertTrue(self.run_stage())
        self.assertTrue(self.targets[0].with_suffix('.uexp').is_file())

    def test_installed_generator_reuses_sprites_for_shop_and_stat_changes(self):
        ffbe=self.root/'raw';ffbe.mkdir();(ffbe/'unit.png').write_bytes(b'art')
        unit={'id':13501,'key':'unit','en':'Unit','donor':13110,'ffbe':{'dir':'raw','id':'123'}}
        called=[]
        def sprites(unit):
            called.append(unit['id'])
            for p in sprite_targets(self.out,unit['id']):
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'asset');p.with_suffix('.uexp').write_bytes(b'exports')
        env={'ROOT':self.root,'OUT':self.out,'LEGACY':self.root/'legacy','USMAP':self.root/'map.usmap',
             'FFRDT':['native-reader'],'ffrenv':SimpleNamespace(game_root=lambda:self.root/'game'),
             'run':lambda cmd:None,'generate_sprites':sprites}
        sequence=SimpleNamespace(build=lambda *a:None)
        audio=SimpleNamespace(build=lambda *a:None)
        with mock.patch.dict(sys.modules,{'ffbe_resonance':sequence,'ffbe_audio':audio}), mock.patch(
                '_ffr_deck_sync.game_identity',return_value={'sha256':'game'}), mock.patch.object(reuse,'code_identity',return_value='tools'):
            reuse.install(env)
            try:
                env['generate_sprites'](unit)
                shutil.rmtree(self.out)
                env['generate_sprites']({**unit,'price':1,'stats':{'Attack':100},'studioAcquisition':{'location':'mitra_shop'}})
                self.assertEqual(called,[13501])
                self.assertEqual(len(list(self.out.rglob('*.uasset'))),9)
                env['generate_sprites']({**unit,'icon':{'style':'custom'}})
                self.assertEqual(called,[13501,13501])
            finally:reuse._active=None

    def test_native_patch_recipe_tracks_json_acb_mapping_and_original_asset(self):
        self.action();mapping=self.root/'map.usmap';mapping.write_bytes(b'mapping')
        recipe=self.root/'build/patch.json';recipe.parent.mkdir(exist_ok=True)
        recipe.write_text(json.dumps({'legacyRoot':str(self.out),'outRoot':str(self.out),
            'tables':[{'asset':'example','add':[],'set':[]}]}))
        c=Cache(self.root,{},['ffr-dt'])
        info=c.command(['ffr-dt','patch',str(recipe),'--usmap',str(mapping)])
        self.assertEqual(info[0],'patch');self.assertIn(mapping,info[2] if isinstance(info[2][0],Path) else [Path(p) for p in info[2]])
        self.assertEqual(info[3],self.targets)
        self.assertIsNone(c.command(['retoc','to-zen','source','destination']))
        recipe.write_text(json.dumps({'legacyRoot':str(self.out),'outRoot':str(self.out),'unknownEdits':[]}))
        self.assertIsNone(c.command(['ffr-dt','patch',str(recipe)]))

    def test_mastery_and_acquisition_changes_reuse_sprites_but_motion_changes_do_not(self):
        import _ffr_incremental as inc
        source=self.root/'tools/_ffr_sephira.py';source.parent.mkdir()
        current=(ROOT/'assets/existing_visions/payload/_ffr_sephira.py').read_text()
        source.write_text(current)
        cache=Cache(self.root,{'game':'one'});inc._sprite_dependencies(cache)
        def stage():return cache.execute('sprites',{'nativeCaster':True},[source],self.targets,self.action)
        self.assertFalse(stage());self.assertTrue(stage())
        source.write_text(current.replace("'sephira_13124','sephira_13118'","'sephira_13124','sephira_13100'"))
        self.assertTrue(stage());self.assertEqual(self.calls,1)
        # Only source normalization is scoped to sprites. Other asset stages
        # must see the real source hash so they rebuild changed rewards.
        self.assertFalse(cache.execute('tables',{},[source],self.targets,self.action))
        source.write_text(current.replace("policy.get('modelMotions', {})", "policy.get('changedMotions', {})"))
        self.assertFalse(stage());self.assertEqual(self.calls,3)


if __name__=='__main__':unittest.main()
