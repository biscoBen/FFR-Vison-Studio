"""Imported icon framing, clipping and real installed converter wiring."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw
from test_existing_visions import ROOT, module, installer, fina_installer

icons = module('native_icons', ROOT / 'assets/existing_visions/payload/_ffr_build_icons.py')


class NativeIconTests(unittest.TestCase):
    def donors(self, root):
        for kind, size in [('face', 128), ('timeline', 128), ('ability', 64)]:
            base = Image.new('RGBA', (size, size), (170, 180, 190, 255))
            mask = Image.new('L', base.size); ImageDraw.Draw(mask).rectangle((10, 10, size-11, size-11), fill=255)
            base.paste((250, 0, 0, 255), (0, 0), mask)
            base.save(root / f'{kind}_13110.png'); mask.save(root / f'{kind}_mask.png')

    def test_native_rim_is_identical_and_donor_portrait_and_ffbe_badges_are_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.donors(root)
            art=Image.new('RGBA',(4,2),(20,30,80,255))
            for kind,size in [('face',128),('timeline',128),('ability',64)]:
                before=Image.open(root/f'{kind}_13110.png');mask=Image.open(root/f'{kind}_mask.png')
                result=icons.render(kind,art,size,root)
                for y in range(size):
                    for x in range(size):
                        if mask.getpixel((x,y))==0:self.assertEqual(result.getpixel((x,y)),before.getpixel((x,y)))
                self.assertEqual(result.getpixel((size//2,size//2)),(20,30,80,255))
                self.assertNotIn((250,0,0,255),result.getdata())
                self.assertEqual(result.tobytes(),icons.render(kind,art,size,root,{'chips':{'NV':3},kind:{'chipScale':8}}).tobytes())
                moved=icons.render(kind,art,size,root,{kind:{'iconX':2.0}})
                self.assertEqual(moved.getpixel((size//2,size//2))[3],0)

    def test_generated_preview_and_bgra_use_native_frame_for_old_saved_border_and_gem_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);tools=root/'tools';tools.mkdir();donors=root/'build/icons/donors';donors.mkdir(parents=True)
            self.donors(donors);script=tools/'_ffr_build_icons.py';shutil.copyfile(ROOT/'assets/existing_visions/payload/_ffr_build_icons.py',script)
            art=root/'sprites';art.mkdir();Image.new('RGBA',(4,2),(20,30,80,255)).save(art/'unit_icon_1.png')
            for style in ['border','gem']:
                out=root/style
                run=subprocess.run([sys.executable,str(script),str(art),'1',str(out),'--style',style,'--rarity','NV'],capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                for kind,size in [('face',128),('timeline',128),('ability',64)]:
                    with Image.open(out/(kind+'.png')) as image:
                        self.assertEqual(image.size,(size,size))
                        self.assertEqual((out/(kind+'.bgra')).read_bytes(),image.tobytes('raw','BGRA'))
                        self.assertEqual(image.tobytes(),icons.render(kind,Image.open(art/'unit_icon_1.png'),size,donors).tobytes())
            source=(ROOT/'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
            patched=installer.hook_builder(fina_installer.hook_builder(source)).decode('utf-8-sig')
            function=next(n for n in ast.parse(patched).body if isinstance(n,ast.FunctionDef) and n.name=='generate_sprites')
            self.assertIn('_ffr_build_icons.py',ast.unparse(function))
            self.assertNotIn('ffbe2ss6\', \'build_icons.py',ast.unparse(function))

    def test_advanced_preview_uses_same_renderer_and_keeps_layout_offsets(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);donors=root/'build/icons/donors';donors.mkdir(parents=True);self.donors(donors)
            module=SimpleNamespace();icons.install_preview({'ROOT':root,'build_icons':module})
            art=Image.new('RGBA',(4,2),'blue');layout={'face':{'iconX':.2}}
            self.assertEqual(module.render('face',art,128,'border','NV',layout).tobytes(),icons.render('face',art,128,donors,layout).tobytes())


if __name__=='__main__':unittest.main()
