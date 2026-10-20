"""Fresh builds must not depend on shipped/prior-build native UI layout JSON."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'assets/existing_visions/payload'))
import _ffr_existingvisions as native
from test_deck_sync import fixture


def raw_layout(scale=.9):
    prop = lambda name, value: {'Name':name, 'Value':value}
    values = [prop('bOverrideOffset',False), prop('bOverrideScale',True), prop('Scale',scale),
              prop('bOverrideFlippedHorizontally',True), prop('bFlippedHorizontally',False),
              prop('Offset', [{'Name':'X','Value':100}])]
    return {'Exports':[{'Data':[{'$type':'UAssetAPI.PropertyTypes.Objects.MapPropertyData, UAssetAPI',
        'Name':'LayoutOverrideDataMap','Value':[[prop('Key',13108),prop('Value',values)]]}]}]}


class MenuLayoutTests(unittest.TestCase):
    def test_real_patched_builder_layout_block_runs_without_the_old_check_directory(self):
        from test_existing_visions import installer, fina_installer
        source=(ROOT/'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        patched=installer.hook_builder(fina_installer.hook_builder(source))
        main=next(n for n in ast.parse(patched).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        first=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='layout')
        last=next(i+1 for i,n in enumerate(main.body) if isinstance(n,ast.If) and ast.unparse(n.test)=='over')
        block=ast.Module(body=main.body[first:last],type_ignores=[])
        with tempfile.TemporaryDirectory() as temp:
            legacy=Path(temp)/'extracted/legacy'
            package=legacy/('FFRS/Content/'+native.MENU_LAYOUT+'.uasset')
            package.parent.mkdir(parents=True);package.write_bytes(b'current native layout')
            units=[{'id':13503+i,'ffbe':{'id':name}} for i,name in enumerate(('fina','agrias','alaya'))]
            def run(args):Path(args[3]).write_text(json.dumps(raw_layout(1.1)))
            for roster in (units,[*units,{'id':13506,'donor':13108}]):
                env={'UNITS':roster,'objects':[],'LEGACY':str(legacy),'_ffr_existingvisions':native,
                     'FFRDT':['native-tool'],'USMAP':'map.usmap','run':run}
                exec(compile(block,'actual_builder_layout','exec'),env)
                values=env['objects'][0]['mapAdd']['LayoutOverrideDataMap']
                self.assertEqual([values[str(13503+i)]['Scale'] for i in range(3)],[2.52]*3)
                if len(roster)==4:self.assertEqual(values['13506']['Scale'],1.1)
                self.assertFalse((Path(temp)/'build/visions_mod/check').exists())

    def test_imported_or_empty_roster_needs_no_layout_dump_or_extraction(self):
        for units in ([],[{'ffbe':{'id':'native-fina'}}],[{'ffbe':{'id':'agrias'}}]):
            self.assertEqual(native.menu_layout({},units),[])

    def test_donor_layout_is_fresh_native_data_and_never_a_shipped_build_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);legacy=root/'extracted/legacy'
            source=legacy/('FFRS/Content/'+native.MENU_LAYOUT+'.uasset')
            source.parent.mkdir(parents=True);source.write_bytes(b'native current asset')
            stale=root/'build/visions_mod/check/da/DA_UIUnitSsLayout.json'
            stale.parent.mkdir(parents=True);stale.write_text('stale shipped layout must not be read')
            view=raw_layout();calls=[]
            def run(args):
                self.assertEqual(args[:3],['native-tool','tojson',str(source)])
                Path(args[3]).write_text(json.dumps(view));calls.append(args)
            env={'LEGACY':legacy,'FFRDT':['native-tool'],'USMAP':'native.usmap','run':run}
            result=native.menu_layout(env,[{'donor':13108}])
            self.assertEqual(result,[{'Key':13108,'Value':{'bOverrideOffset':False,'bOverrideScale':True,
                'Scale':.9,'bOverrideFlippedHorizontally':True,'bFlippedHorizontally':False}}])
            view=raw_layout(1.25)
            self.assertEqual(native.menu_layout(env,[{'donor':13108}])[0]['Value']['Scale'],1.25)
            self.assertEqual(len(calls),2)
            self.assertEqual(stale.read_text(),'stale shipped layout must not be read')

    def test_missing_source_extracts_only_official_containers(self):
        with tempfile.TemporaryDirectory() as temp:
            root,game,env,*_=fixture(Path(temp))
            legacy=root/'extracted/legacy';source=legacy/('FFRS/Content/'+native.MENU_LAYOUT+'.uasset')
            mods=game/'FFRS/Content/Paks/~mods';mods.mkdir(parents=True)
            (mods/'private-mod.utoc').write_bytes(b'Never read this as native')
            env.update(LEGACY=legacy,FFRDT=['table-reader'],USMAP='map.usmap')
            env['ffrenv'].RETOC='retoc'
            calls=[]
            def run(args):
                calls.append(args)
                if args[0]=='retoc':
                    view=Path(args[-2])
                    self.assertEqual([p.name for p in view.iterdir()],['FFRS-Windows.utoc'])
                    self.assertFalse((view/'~mods').exists())
                    source.parent.mkdir(parents=True);source.write_bytes(b'official native source')
                else:Path(args[3]).write_text(json.dumps(raw_layout()))
            env['run']=run
            self.assertEqual(native.menu_layout(env,[{'donor':13108}])[0]['Value']['Scale'],.9)
            self.assertEqual([c[0] for c in calls],['retoc','table-reader'])

    def test_invalid_native_layout_fails_without_substituting_old_data(self):
        for change in ('missing','ambiguous','duplicate','bad_scale','bad_flag'):
            view=raw_layout()
            value=view['Exports'][0]['Data'][0]
            if change=='missing':view['Exports']=[]
            elif change=='ambiguous':view['Exports']*=2
            elif change=='duplicate':value['Value']*=2
            elif change=='bad_scale':value['Value'][0][1]['Value'][2]['Value']='NaN'
            else:value['Value'][0][1]['Value'][0]['Value']=1
            with self.subTest(change=change),self.assertRaises(ValueError):native.decode_menu_layout(view)


if __name__=='__main__':unittest.main()
