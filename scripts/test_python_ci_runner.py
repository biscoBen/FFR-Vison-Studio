"""A failed discovered test must still fail CI and expose its real traceback."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class PythonRunnerTests(unittest.TestCase):
    def test_discovered_failure_returns_nonzero_and_an_actionable_annotation(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'test_example.py').write_text(
                'import unittest\nclass Example(unittest.TestCase):\n'
                '    def test_expected_failure(self):\n        self.fail("explicit runner fixture failure")\n')
            runner=Path(__file__).resolve().with_name('run_python_tests.py')
            result=subprocess.run([sys.executable,str(runner),'-s',folder,'-p','test_example.py'],
                                  capture_output=True,text=True,timeout=20,
                                  env={**os.environ,'GITHUB_ACTIONS':'true'})
            self.assertEqual(result.returncode,1)
            self.assertIn('::error title=Python regression::',result.stdout)
            self.assertIn('explicit runner fixture failure',result.stdout)
            self.assertIn('Ran 1 test',result.stderr)


if __name__=='__main__':unittest.main()
