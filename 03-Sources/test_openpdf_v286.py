import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from windows_window_probe_v286 import matching_window, visible_windows
import smoke_windows_v286 as smoke

class WindowsWindowProbeTests(unittest.TestCase):
    def test_match_title_case_insensitive(self):
        self.assertEqual(matching_window(5, enumerate_windows=lambda pid:[{'hwnd':10,'title':'OpenPDF Studio V28.6'}])['hwnd'],10)
    def test_reject_other_window(self):
        self.assertIsNone(matching_window(5, enumerate_windows=lambda pid:[{'hwnd':2,'title':'Unrelated'}]))
    def test_empty_window_list(self):
        self.assertIsNone(matching_window(5, enumerate_windows=lambda pid:[]))
    def test_platform_guard(self):
        with patch('windows_window_probe_v286.sys.platform','linux'):
            with self.assertRaises(RuntimeError): visible_windows(1)
    def test_missing_executable_reports_failure(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(smoke.qualify(root=Path(d))['status'],'FAIL')
    def test_build_targets_current_entrypoint(self):
        build=(Path(__file__).parent/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertRegex(build, r'openpdf_windows_v\d+\.py')
        self.assertRegex(build, r'smoke_windows_v\d+\.py')

if __name__=='__main__': unittest.main()
