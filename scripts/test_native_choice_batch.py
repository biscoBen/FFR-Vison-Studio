"""Batched menus retain distinct tags/signatures and need no native calls on reuse."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT,module,installer,fina_installer
import _ffr_testing as testing
import _ffr_build_cache as reuse


class NativeChoiceBatchTests(unittest.TestCase):
    def test_batch_preserves_each_dialog_and_reuses_all_outputs_in_a_fresh_folder(self):
        with mock.patch.dict('sys.modules',{'ffbe_lb':SimpleNamespace(NEUTRAL_COLOR='#808080')}):
            seq=module('batch_sequence_fixture',ROOT/'scripts/fixtures/engine_motion/ffbe_resonance.py')
        source=json.loads(gzip.decompress((ROOT/'scripts/fixtures/practice_dialog/shell.json.gz').read_bytes()))
        with tempfile.TemporaryDirectory() as directory,mock.patch.dict('sys.modules',{'ffbe_resonance':seq}):
            root=Path(directory);out=root/'out';legacy=root/'legacy';work=root/'work'
            native=legacy/(seq.SHELL+'.uasset');native.parent.mkdir(parents=True);native.write_bytes(b'shell')
            native.with_suffix('.uexp').write_bytes(b'exports');views={str(native):source};calls=[]
            def write(path,view):
                views[str(path)]=copy.deepcopy(view);path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'asset');path.with_suffix('.uexp').write_text(json.dumps(view))
            def rename(value,pairs):
                if isinstance(value,str):
                    for old,new in pairs:value=value.replace(old,new)
                    return value
                if isinstance(value,list):return [rename(v,pairs) for v in value]
                if isinstance(value,dict):return {k:rename(v,pairs) for k,v in value.items()}
                return value
            def run(cmd):
                calls.append(cmd[1]);op=cmd[1]
                if op=='tojson':Path(cmd[3]).write_text(json.dumps(views[str(Path(cmd[2]))]))
                elif op=='clone-package':
                    write(Path(cmd[3]),rename(views[str(Path(cmd[2]))],[(cmd[4],cmd[5]),tuple(cmd[6].split('=',1))]))
                elif op=='fromjson':write(Path(cmd[3]),json.loads(Path(cmd[2]).read_bytes()))
                elif op=='patch':
                    recipe=json.loads(Path(cmd[2]).read_bytes())
                    for clone in recipe.get('clones',[]):
                        original=Path(recipe['legacyRoot'])/(clone['from']+'.uasset')
                        write(Path(recipe['outRoot'])/(clone['to']+'.uasset'),rename(views[str(original)],clone['rename']))
                    for change in recipe.get('objects',[]):
                        p=Path(recipe['outRoot'])/(change['asset']+'.uasset');view=views[str(p)]
                        owner=next(e for e in view['Exports'] if e['ObjectName']==change['export'])
                        for name,value in change['set'].items():seq.child(owner['Data'],name)[0]['Value']=value
                        write(p,view)
                else:raise AssertionError(op)
            env={'ROOT':root,'OUT':out,'LEGACY':legacy,'BUILD':work,'USMAP':str(root/'Mappings.usmap'),'FFRDT':['native'],'run':run}
            names=['Studio_Menu_A','Studio_Menu_B','Studio_Menu_C']
            with mock.patch.object(reuse,'_active',reuse.Cache(root,{'game':'fixture'})):
                testing.build_choices(env,names,'FFRS/Content/Studio/','menus')
                self.assertEqual(len(calls),8)  # formerly four processes per menu
                signatures=[]
                for name in names:
                    path=out/('FFRS/Content/Studio/SEQ_'+name+'.uasset');view=views[str(path)]
                    testing.verify_practice_choice(view,'UI.Dialog.Choice.'+name)
                    scene=next(e for e in view['Exports'] if e['ObjectName']=='MovieScene_0')
                    signatures.append(seq.child(scene['Data'],'Signature')[0]['Value'])
                self.assertEqual(len(set(signatures)),3)
                before=len(calls);shutil.rmtree(out)
                testing.build_choices(env,names,'FFRS/Content/Studio/','menus')
                self.assertEqual(len(calls),before)
                self.assertEqual(len(list(out.rglob('*.uasset'))),3)
                self.assertEqual(reuse._active.stats['dialogs']['reused'],1)

    def test_installed_builder_checks_cave_write_before_sprite_generation(self):
        import ast
        source=installer.hook_builder(fina_installer.hook_builder((ROOT/'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()))
        main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        calls=[n for n in ast.walk(main) if isinstance(n,ast.Call)]
        preflight=next(n for n in calls if ast.unparse(n.func)=='_ffr_shrine_challenges.preflight')
        sprites=[n for n in calls if ast.unparse(n.func)=='generate_sprites']
        self.assertTrue(sprites)
        self.assertLess(preflight.lineno,min(n.lineno for n in sprites))


if __name__=='__main__':unittest.main()
