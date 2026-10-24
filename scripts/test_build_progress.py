"""Timestamped logs, actual operation duration, failed-run profiles and streaming."""
import ast
import gzip
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT,installer
import _ffr_build_progress as progress
import _ffr_build_cache as reuse


class BuildProgressTests(unittest.TestCase):
    def test_stamp_includes_wall_clock_and_elapsed_build_time(self):
        line=progress.stamp('native output',1700000000,now=1700000066.25)
        self.assertRegex(line,r'^\[\d{4}-\d\d-\d\dT.* \+01:06\.2\] native output$')

    def test_failed_operation_still_records_durations_and_cache_counts(self):
        with tempfile.TemporaryDirectory() as root,mock.patch.dict(progress.os.environ,{'FFR_LOG_DIR':root}),mock.patch.object(reuse,'_active',None):
            clock=[0.0];stages=[];profile=progress.Profile(root,stages.append,clock=lambda:clock[0])
            profile.stage('Converting sprites and icons: First (1 of 2)')
            clock[0]=2;profile.stage('Building challenge menus')
            def fail():clock[0]=5;raise ValueError('fixture failure')
            with self.assertRaisesRegex(ValueError,'fixture failure'):profile.operation('fromjson cave',fail)
            clock[0]=6;profile.finish();profile.finish()
            report=json.loads(next(Path(root).glob('build-profile-*.json')).read_bytes())
            self.assertEqual(report['phaseTotals'],{'Converting sprites and icons':2,'Building challenge menus':4})
            self.assertEqual(report['operations'][0]['seconds'],3)
            self.assertEqual(report['operations'][0]['status'],'failed')
            self.assertTrue(report['operationFailed'])
            events=[json.loads(s) for s in next(Path(root).glob('build-events-*.jsonl')).read_text().splitlines()]
            self.assertEqual(events[-1]['event'],'profile-end')
            self.assertEqual(stages,['Converting sprites and icons: First (1 of 2)','Building challenge menus'])

    def test_server_console_and_persisted_log_get_identical_timestamps(self):
        source=installer.hook_server(gzip.decompress((ROOT/'scripts/fixtures/existing_visions/server.py.gz').read_bytes()))
        tree=ast.parse(source);build=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_build')
        note=next(n for n in build.body if isinstance(n,ast.FunctionDef) and n.name=='note')
        saved=io.StringIO();env={'state':{'log':[],'started':0},'logf':saved}
        exec(compile(ast.Module(body=[note],type_ignores=[]),'server_note','exec'),env)
        env['note']('native tool line')
        self.assertTrue(env['state']['log'][0].startswith('['))
        self.assertEqual(saved.getvalue(),env['state']['log'][0]+'\n')
        self.assertIn('_ffr_build_progress.capture',source.decode('utf-8-sig'))

    def test_verification_lines_are_delivered_before_process_finishes(self):
        received=[]
        class Process:
            stdout=io.StringIO('first\nsecond\n')
            returncode=0
            def wait(self):
                self.checked=True
                if received!=['first','second']:raise AssertionError('output was buffered until the end')
        process=Process()
        with mock.patch.object(progress.subprocess,'Popen',return_value=process):
            result=progress.capture(['verify'],log=received.append,capture_output=True,text=True)
        self.assertEqual(result.returncode,0);self.assertTrue(process.checked)


if __name__=='__main__':unittest.main()
