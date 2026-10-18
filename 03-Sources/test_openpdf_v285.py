import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import smoke_windows_v285 as smoke

class WindowsQualificationTests(unittest.TestCase):
    def test_missing_exe_writes_failure_json(self):
        with tempfile.TemporaryDirectory() as temp:
            report=smoke.qualify(root=Path(temp))
            self.assertEqual(report['status'],'FAIL')
            self.assertIn('Missing packaged executable',report['error'])
    def test_bad_exe_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); exe=smoke.executable(root);exe.parent.mkdir(parents=True)
            exe.write_bytes(b'ELF' + b'x'*100)
            with self.assertRaisesRegex(RuntimeError,'PE header'):smoke.verify_static(root)
    def test_static_exe_and_internal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);exe=smoke.executable(root);exe.parent.mkdir(parents=True)
            exe.write_bytes(b'MZ'+b'x'*100);(exe.parent/'_internal').mkdir()
            self.assertTrue(smoke.verify_static(root)['pe_header'])
    def test_runtime_rejects_non_windows(self):
        with patch.object(smoke.sys,'platform','linux'):
            with self.assertRaisesRegex(RuntimeError,'requires Windows'):smoke.verify_launch()
    def test_build_and_qualifier_consistent(self):
        root=Path(__file__).parent
        build=(root/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertRegex(build, r'openpdf_windows_v\d+\.py')
        self.assertRegex(build, r'smoke_windows_v\d+\.py --static')
        self.assertRegex(build, r'test_openpdf_v\d+')
        self.assertIn('smoke_windows_v285.py --launch', (root/'QUALIFY-WINDOWS-V28.5.cmd').read_text())
    def test_failure_report_saved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); target=root/'report.json'
            with patch.object(smoke,'ROOT',root), patch.object(smoke,'verify_static',side_effect=RuntimeError('synthetic error')):
                self.assertEqual(smoke.main(['--static','--output',str(target)]),1)
            self.assertEqual(json.loads(target.read_text())['status'],'FAIL')

if __name__=='__main__':unittest.main()
