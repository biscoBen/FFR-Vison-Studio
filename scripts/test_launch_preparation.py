"""Exercise local transfer/rollback, new-build gates and actual launch API requests."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'assets/existing_visions/payload'))
import _ffr_launch as launch
import _ffr_deck_sync as transfer
from test_deck_sync import fixture


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root, self.game, self.env, *_ = fixture(self.base)
        self.env.update(state={'running': False}, setup_state={'running': False})
        self.units = [{'id': 13500, 'key': 'fina', 'en': 'Crystal Fina', 'skills': {'471010': {'from': 220020}},
                       'stats': {'Attack': 19}, 'acquisition': {'cave': {'x': 12, 'y': 50}}, 'testAcquire': True}]
        transfer.json_write(self.root/'mods/EstherTsukiko/units.json', self.units)
        transfer.json_write(self.root/launch.PREPARED, {'schema': 1, 'gameIdentity': transfer.game_identity(self.game)})

    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        app = FastAPI()
        launch.register(app, self.env)
        return TestClient(app)

    def test_studio_backup_restore_keeps_config_and_credentials_local_and_rolls_back_previous_roster(self):
        (self.root/'config.json').write_text('PC paths')
        (self.root/transfer.SETTINGS).write_text('private repository credentials sentinel')
        archive=self.base/'backup.zip'
        launch.backup(self.root,archive)
        with zipfile.ZipFile(archive) as bundle:
            self.assertNotIn('config.json',bundle.namelist())
            self.assertNotIn(transfer.SETTINGS,bundle.namelist())
            self.assertNotIn('private repository',str(bundle.read('manifest.json')))
        original=archive.read_bytes()
        transfer.json_write(self.root/'mods/EstherTsukiko/units.json', [])
        previous=launch.replace_inputs(self.root,launch.read_backup(original))
        self.assertEqual(json.loads((self.root/'mods/EstherTsukiko/units.json').read_bytes()),self.units)
        undo=launch.read_backup((self.root/launch.HOME/'backups'/previous).read_bytes())
        self.assertEqual(json.loads(undo['mods/EstherTsukiko/units.json']),[])
        self.assertEqual((self.root/'config.json').read_text(),'PC paths')
        self.assertTrue((self.root/transfer.SETTINGS).exists())
        self.assertFalse((self.root/transfer.VERIFIED).exists())

    def test_corrupt_and_traversal_backups_change_nothing(self):
        before=launch.input_bytes(self.root)
        invalid=io.BytesIO()
        with zipfile.ZipFile(invalid,'w') as bundle:
            bundle.writestr('manifest.json',json.dumps({'schema':1,'kind':'ffr-studio-backup','files':{}}))
            bundle.writestr('../config.json','bad')
        for raw in (b'not a ZIP',invalid.getvalue()):
            with self.assertRaises(ValueError): launch.read_backup(raw)
        self.assertEqual(launch.input_bytes(self.root),before)

    def test_original_preset_keeps_kits_and_has_a_complete_undo(self):
        import _ffr_ability_modes as a
        import _ffr_sephira as s
        import _ffr_testing as t
        transfer.json_write(self.root/a.CONFIG,{'schema':1,'showUnverified':True,'useChanges':True,'useNativeRepairs':True})
        transfer.json_write(self.root/t.CONFIG,{'schema':1,'maxMr':True,'practiceBattle':True,'surviveAtOne':True,'ffbeNeedles':True,'fieldLeader':True})
        before=launch.input_bytes(self.root)
        saved=launch.original_preset(self.root)
        self.assertEqual(launch.flags(self.root)['enabledPatches'],[])
        self.assertFalse(t.settings(self.root)['surviveAtOne'])
        units=json.loads((self.root/'mods/EstherTsukiko/units.json').read_bytes())
        self.assertEqual(units,[{**self.units[0],'testAcquire':False}])
        launch.replace_inputs(self.root,launch.read_backup((self.root/launch.HOME/'backups'/saved).read_bytes()))
        self.assertEqual(launch.input_bytes(self.root),before)

    def test_failed_config_write_restores_every_previous_file(self):
        before=launch.input_bytes(self.root)
        atomic=transfer.atomic
        once=[False]
        def failing(path,data):
            if str(path).endswith('ability-modes.json') and not once[0]:
                once[0]=True;raise OSError('simulated disk failure')
            return atomic(path,data)
        with mock.patch.object(transfer,'atomic',side_effect=failing), self.assertRaises(OSError):
            launch.original_preset(self.root)
        self.assertEqual(launch.input_bytes(self.root),before)

    def test_new_container_and_changed_inputs_block_old_install(self):
        launch.original_preset(self.root)
        status=launch.guard(self.env)
        launch.capture_build(self.env)
        launch.guard(self.env,installing=True)
        transfer.json_write(self.root/'mods/EstherTsukiko/units.json',[])
        with self.assertRaisesRegex(ValueError,'Rebuild'):launch.guard(self.env,installing=True)
        new=self.game/'FFRS/Content/Paks/patch.utoc';new.write_bytes(b'new native container')
        self.assertFalse(launch.prepared_status(self.env)['prepared'])
        with self.assertRaisesRegex(ValueError,'Prepare'):launch.guard(self.env)
        self.assertNotEqual(status['gameIdentity'],transfer.game_identity(self.game))

    def test_preparation_message_distinguishes_untracked_changed_and_incomplete_data(self):
        current=transfer.game_identity(self.game)
        (self.root/launch.PREPARED).unlink()
        self.assertIn('no recorded game-data baseline',launch.prepared_status(self.env)['message'])
        transfer.json_write(self.root/launch.PREPARED,{'schema':1,'gameIdentity':{'sha256':'other build'}})
        self.assertIn('game files differ',launch.prepared_status(self.env)['message'])
        transfer.json_write(self.root/launch.PREPARED,{'schema':1,'source':'Preparation incomplete'})
        self.assertIn('did not finish',launch.prepared_status(self.env)['message'])
        transfer.json_write(self.root/launch.PREPARED,{'schema':1,'gameIdentity':current})
        self.assertTrue(launch.prepared_status(self.env)['prepared'])

    def test_patch_review_is_fingerprint_specific_and_preset_avoids_review(self):
        with self.assertRaisesRegex(ValueError,'Review enabled patches'):launch.guard(self.env)
        with self.client() as client:
            self.assertEqual(client.post('/api/launch/review-patches',json={'gameSha256':'wrong'}).status_code,409)
            identity=transfer.game_identity(self.game)
            self.assertEqual(client.post('/api/launch/review-patches',json={'gameSha256':identity['sha256']}).status_code,200)
        launch.guard(self.env)
        (self.game/transfer.MARKER).write_bytes(b'updated game')
        self.assertFalse(launch.prepared_status(self.env)['demoPatchReview'])

    def test_local_deck_snapshots_install_replace_remove_runtime_and_restore_without_network(self):
        # Runtime payload also serves Crystal Fina when cycling itself is off.
        from test_deck_sync import sync as tested_transfer
        root,game,env,*_=fixture(self.base/'with-runtime',cycling=True)
        archive=self.base/'snapshot.zip'
        transfer.capture(env)
        with mock.patch.object(transfer.GitHub,'request',side_effect=AssertionError('No network')):
            transfer.local_snapshot(env,archive)
            extracted=self.base/'export';extracted.mkdir()
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(set(bundle.namelist()),{'mod.zip','Install snapshot.sh','Deck Mod Sync.py','Read me.txt'})
                bundle.extractall(extracted)
                self.assertNotIn(str(root),bundle.read('Read me.txt').decode())
                self.assertIn(b'--snapshot',bundle.read('Install snapshot.sh'))
            deck=self.base/'Deck game';(deck/transfer.MARKER).parent.mkdir(parents=True)
            (deck/transfer.MARKER).write_bytes((game/transfer.MARKER).read_bytes())
            sentinel=deck/transfer.PAKS[0];sentinel.parent.mkdir(parents=True);sentinel.write_bytes(b'previous desktop mod')
            state=self.base/'Deck state';state.mkdir()
            result=transfer.import_snapshot(state,deck,extracted/'mod.zip',running=lambda:False)
            self.assertTrue(result['cycling'])
            # A second snapshot without runtime removes stale loader/scripts.
            transfer.json_write(root/'build/field-leader/payload.json',{'schema':1,'files':{}})
            transfer.capture(env);transfer.make_package(env,extracted/'next.zip')
            transfer.import_snapshot(state,deck,extracted/'next.zip',running=lambda:False)
            self.assertFalse((deck/transfer.LEADER/'Scripts/main.lua').exists())
            self.assertTrue(transfer.restore(state,running=lambda:False))
            self.assertEqual(sentinel.read_bytes(),b'previous desktop mod')
            self.assertFalse((deck/transfer.PAKS[1]).exists())

    def test_actual_standalone_deck_cli_accepts_local_snapshot_without_credentials(self):
        transfer.capture(self.env)
        archive=self.base/'local.zip';transfer.make_package(self.env,archive)
        destination=self.base/'Deck';(destination/transfer.MARKER).parent.mkdir(parents=True)
        (destination/transfer.MARKER).write_bytes((self.game/transfer.MARKER).read_bytes())
        isolated=self.base/'home';isolated.mkdir()
        result=subprocess.run([sys.executable,str(ROOT/'assets/existing_visions/payload/_ffr_deck_sync.py'),
            '--snapshot',str(archive),'--game',str(destination),'--root',str(self.base/'state')],
            capture_output=True,text=True,env={**os.environ,'HOME':str(isolated),'USERPROFILE':str(isolated)},timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('No download or build',result.stdout)
        self.assertTrue((destination/transfer.PAKS[0]).exists())
        menu=subprocess.run([sys.executable,str(ROOT/'assets/existing_visions/payload/_ffr_deck_sync.py'),
            '--interactive','--game',str(destination),'--root',str(self.base/'menu-state')],
            input='1\n'+str(archive)+'\n',capture_output=True,text=True,
            env={**os.environ,'HOME':str(isolated),'USERPROFILE':str(isolated)},timeout=20)
        self.assertEqual(menu.returncode,0,menu.stdout+menu.stderr)
        self.assertIn('No download or build',menu.stdout)
        self.assertNotIn('Token (hidden)',menu.stdout)

    def test_snapshot_refuses_changed_settings_before_export_and_other_native_container_before_import(self):
        transfer.capture(self.env)
        transfer.json_write(self.root/'mods/EstherTsukiko/icon_layout.json',{'face':{'x':15}})
        with self.assertRaisesRegex(transfer.SyncError,'settings'):transfer.make_package(self.env,self.base/'bad.zip')
        transfer.capture(self.env);transfer.make_package(self.env,self.base/'good.zip')
        deck=self.base/'different';(deck/transfer.MARKER).parent.mkdir(parents=True)
        (deck/transfer.MARKER).write_bytes((self.game/transfer.MARKER).read_bytes())
        (deck/'FFRS/Content/Paks/extra.utoc').write_bytes(b'new build')
        state=self.base/'state';state.mkdir()
        with self.assertRaisesRegex(transfer.SyncError,'version differs'):
            transfer.import_snapshot(state,deck,self.base/'good.zip',running=lambda:False)
        self.assertFalse((deck/transfer.PAKS[0]).exists())

    def test_api_backup_preview_rejects_stale_restore_and_results_are_separate_per_game(self):
        with self.client() as client:
            response=client.get('/api/launch/studio-backup');self.assertEqual(response.status_code,200)
            preview=client.post('/api/launch/backup/preview',content=response.content).json()
            self.assertEqual(preview['units'],['Crystal Fina'])
            transfer.json_write(self.root/'mods/EstherTsukiko/units.json',[])
            stale=client.post('/api/launch/backup/restore',content=response.content,headers={'If-Match':preview['inputsSha256']})
            self.assertEqual(stale.status_code,409)
            preview=client.post('/api/launch/backup/preview',content=response.content).json()
            restored=client.post('/api/launch/backup/restore',content=response.content,headers={'If-Match':preview['inputsSha256']})
            self.assertEqual(restored.status_code,200,restored.text)
            self.assertTrue(client.get('/api/launch/status').json()['revision'])
            stale_save=client.put('/api/spec',json=[],headers={'X-Launch-Revision':'before-restore'})
            self.assertEqual(stale_save.status_code,409)
            self.assertIn('Reload',stale_save.json()['detail'])
            identity=transfer.game_identity(self.game)
            saved=client.post('/api/launch/tests',json={'gameSha256':identity['sha256'],'observations':{
                'skill-500270':{'visuals':'fail','direction':'untested','sound':'pass','timing':'untested','notes':'original enemy'}}})
            self.assertEqual(saved.status_code,200,saved.text)
            self.assertIn('original enemy',client.get('/api/launch/tests.csv').text)
            (self.game/transfer.MARKER).write_bytes(b'a different native build')
            self.assertEqual(client.get('/api/launch/status').json()['results']['observations'],{})

    def test_async_export_streams_a_complete_local_package_and_never_uploads(self):
        launch.original_preset(self.root)
        launch.capture_build(self.env)
        transfer.capture(self.env)
        with self.client() as client, mock.patch.object(transfer.GitHub,'request',side_effect=AssertionError('No upload')):
            started=client.post('/api/launch/deck-export')
            self.assertEqual(started.status_code,200,started.text)
            for _ in range(100):
                state=client.get('/api/launch/status').json()
                if not state['job']['running']: break
                time.sleep(.01)
            self.assertEqual(state['job']['result'],'ok',state['job'])
            response=client.get('/api/launch/exports/'+state['job']['download'])
            self.assertEqual(response.status_code,200)
            with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
                self.assertIn('mod.zip',bundle.namelist())
                with zipfile.ZipFile(io.BytesIO(bundle.read('mod.zip'))) as mod:
                    self.assertEqual(set(json.loads(mod.read('manifest.json'))['files']),set(transfer.PAKS))

    def test_compare_detects_actual_routes_and_inventory_but_ignores_localized_name_only(self):
        baseline=copy.deepcopy(launch.bundled('launch_demo.json.gz'))
        current=copy.deepcopy(baseline)
        for row in current['skills'].values():row['name']=None
        self.assertEqual(launch.compare(baseline,current)['skills'],{})
        current['skills']['500270']['routes']=[{'ID':500271,'LevelSequence':'/Game/ActualNewNeedles'}]
        current['inventory'].append('FFRS/Content/ActualNewNeedles.uasset')
        difference=launch.compare(baseline,current)
        self.assertEqual(set(difference['skills']),{'500270'})
        self.assertIn('ActualNewNeedles',difference['assetsAdded'][0])
        self.assertFalse(difference['inGameValidated'])

    def test_collection_decodes_parallel_tables_with_private_maps_and_downloads_the_reference(self):
        mapping = self.root/'extracted/Mappings.usmap'
        mapping.parent.mkdir(parents=True); mapping.write_bytes(b'explicit mapping fixture')
        self.env['ffrenv'].USMAP = str(mapping)
        self.env['ffrenv'].RETOC = 'retoc'
        self.env['ffrenv'].FFRDT = ['reader']
        barrier = threading.Barrier(4); lock = threading.Lock()
        active, seen, workers = set(), set(), set()
        main = threading.get_ident(); decoded = []
        def run(command, log):
            command = list(map(str,command))
            if command[0] == 'retoc':
                if command[1] == 'list': return 'native\tFFRS/Content/Datatable/Skill/DT_SkillData.uasset'
                if command[command.index('--filter')+1] == 'Datatable/Skill/':
                    legacy = Path(command[-1])/'FFRS/Content/Datatable/Skill'
                    legacy.mkdir(parents=True)
                    for name in ['DT_SkillData',*[f'Test_{i}' for i in range(8)]]:
                        (legacy/(name+'.uasset')).write_bytes(b'explicit native asset fixture')
                return ''
            self.assertEqual(command[:2],['reader','rows'])
            usmap = Path(command[command.index('--usmap')+1])
            self.assertNotEqual(usmap,mapping)
            self.assertEqual(usmap.read_bytes(),mapping.read_bytes())
            with lock:
                self.assertNotIn(usmap,active,'Concurrent readers shared a mappings file')
                active.add(usmap); seen.add(usmap)
                first = threading.get_ident() not in workers
                workers.add(threading.get_ident())
            try:
                if threading.get_ident() != main and first: barrier.wait(timeout=5)
                transfer.json_write(Path(command[3]),{'rows':{'fixture':{'ID':500270}},'_asset':command[2]})
                decoded.append(command[2])
            finally:
                with lock: active.remove(usmap)
            return ''
        with mock.patch.object(launch,'run',side_effect=run):
            result = launch.collect(self.env,lambda _:None)
        self.assertEqual(len(decoded),9); self.assertEqual(len(seen),4)
        self.assertTrue(all(not path.exists() for path in seen))
        self.assertEqual(mapping.read_bytes(),b'explicit mapping fixture')
        self.assertEqual(launch.record(self.root,launch.HOME+'/latest-reference.json')['folder'],result['folder'])
        with self.client() as client:
            self.assertTrue(client.get('/api/launch/status').json()['latestReference'])
            response = client.get('/api/launch/reference')
            self.assertEqual(response.status_code,200,response.text[:200])
            with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
                self.assertIn('comparison.json',bundle.namelist())
                self.assertEqual(len(json.loads(bundle.read('reference.json'))['tables']),9)

    def test_missing_collection_mapping_stops_before_extracting_and_command_errors_keep_the_cause(self):
        self.env['ffrenv'].USMAP = str(self.root/'extracted/Mappings.usmap')
        with mock.patch.object(launch,'run',side_effect=AssertionError('Must not start extraction')):
            with self.assertRaisesRegex(ValueError,'mappings file is unavailable'): launch.collect(self.env,lambda _:None)
        message = 'System.IO.IOException: Mappings.usmap is being used by another process.\n'+'stack frame\n'*200+'Usmap.PathToStream'
        result = subprocess.CompletedProcess(['reader'],1,stdout='',stderr=message)
        with mock.patch.object(launch.subprocess,'run',return_value=result):
            with self.assertRaises(ValueError) as error: launch.run(['reader'],lambda _:None)
        self.assertIn('being used by another process',str(error.exception))
        self.assertIn('Usmap.PathToStream',str(error.exception))

    def test_failed_reference_job_stops_and_leaves_download_unavailable(self):
        with self.client() as client, mock.patch.object(launch,'collect',side_effect=ValueError('Mappings.usmap sharing failure')):
            self.assertEqual(client.post('/api/launch/collect').status_code,200)
            for _ in range(100):
                state = client.get('/api/launch/status').json()
                if not state['job']['running']: break
                time.sleep(.01)
            self.assertFalse(state['job']['running'])
            self.assertEqual(state['job']['result'],'failed')
            self.assertIn('sharing failure',state['job']['message'])
            self.assertFalse(state['latestReference'])
            self.assertEqual(client.get('/api/launch/reference').status_code,409)

    def test_game_preparation_moves_stale_data_and_ignores_mods_and_shipped_native_catalog(self):
        from types import SimpleNamespace
        (self.root/'extracted/rows').mkdir(parents=True)
        (self.root/'extracted/rows/stale.json').write_text('old demo rows')
        (self.game/'FFRS/Content/Paks/~mods').mkdir()
        (self.game/'FFRS/Content/Paks/~mods/other.utoc').write_text('another mod')
        setup=SimpleNamespace(SHIPPED=[('ffr_catalog.json','build/devui/ffr_catalog.json'),('Mappings.usmap','extracted/Mappings.usmap')],
                              EXTRACT_FILTERS=['Datatable'])
        original_shipped=setup.SHIPPED
        seen=[]
        setup._listing=lambda *args:None
        def extract(view,log):
            self.assertFalse((Path(view)/'~mods').exists())
            seen.extend(p.name for p in Path(view).iterdir())
        setup._extract=extract
        def prepare(game,log):
            self.assertNotIn('ffr_catalog.json',[a for a,b in setup.SHIPPED])
            setup._extract('ignored',log)
            setup._listing('ignored',log)
        setup.prepare=prepare
        self.env['ffrenv'].RETOC='retoc'
        # Force a different fingerprint from the previous prepared record.
        (self.game/transfer.MARKER).write_bytes(b'full game source')
        with mock.patch.object(launch,'run',return_value='FFRS header ExportBundleData ../../../FFRS/Content/Datatable/Skill/DT_SkillData.uasset'):
            launch.prepare_game(self.game,setup,self.env,lambda _:None)
        self.assertEqual(seen,['FFRS-Windows.utoc'])
        self.assertIs(setup.SHIPPED,original_shipped)
        self.assertTrue(list((self.root/launch.HOME/'prepared-backups').glob('*/extracted/rows/stale.json')))
        self.assertTrue(launch.prepared_status(self.env)['prepared'])
        self.assertNotIn('old demo rows',(self.root/'extracted/utoc_filelist.tsv').read_text())

    def test_failed_preparation_invalidates_old_identity_before_switching_back(self):
        from types import SimpleNamespace
        old=transfer.game_identity(self.game)
        (self.root/'extracted').mkdir()
        (self.root/'extracted/original.txt').write_text('original source')
        setup=SimpleNamespace(SHIPPED=[],EXTRACT_FILTERS=[],_listing=lambda *a:None,_extract=lambda *a:None)
        def fail(*args,**kwargs):
            (self.root/'extracted').mkdir(exist_ok=True)
            (self.root/'extracted/partial.txt').write_text('partial new game source')
            raise ValueError('simulated changed mapping')
        setup.prepare=fail
        (self.game/transfer.MARKER).write_bytes(b'new game build')
        with self.assertRaisesRegex(ValueError,'changed mapping'):
            launch.prepare_game(self.game,setup,self.env,lambda _:None)
        self.assertNotEqual(launch.record(self.root,launch.PREPARED).get('gameIdentity'),old)
        self.assertFalse(launch.prepared_status(self.env)['prepared'])
        (self.game/transfer.MARKER).write_bytes(b'explicit synthetic game version fixture')
        def success(*args,**kwargs):
            self.assertFalse((self.root/'extracted/partial.txt').exists())
        setup.prepare=success
        launch.prepare_game(self.game,setup,self.env,lambda _:None)
        self.assertTrue(launch.prepared_status(self.env)['prepared'])
        self.assertEqual(len(list((self.root/launch.HOME/'prepared-backups').glob('*/extracted/*'))),2)

    def test_bundled_test_sheet_preserves_waterga_ambiguity_and_distinguishes_imported_failures(self):
        tests=launch.bundled('launch_tests.json')['tests']
        self.assertEqual(len({x['key'] for x in tests}),len(tests))
        water=next(x for x in tests if x['name']=='Waterga')
        self.assertEqual(water['skillIds'],[250150,255110])
        self.assertIn('unresolved',water['source'])
        gloom=next(x for x in tests if x['name']=='Blighted Gloom')
        self.assertEqual(gloom['skillIds'],[407050])
        self.assertIn('not established',gloom['source'])


if __name__ == '__main__':unittest.main()
