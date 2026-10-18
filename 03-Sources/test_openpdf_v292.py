import unittest
from pathlib import Path
from unittest.mock import patch
import smoke_windows_v292 as smoke
import qualify_installer_v292 as installer
from windows_window_probe_v286 import window_rectangle
ROOT=Path(__file__).parent
class V292Tests(unittest.TestCase):
    def test_default_timeout(self):
        self.assertEqual(smoke.qualify.__defaults__[4],12)
    def test_screenshot_window_bounds_required(self):
        src=(ROOT/'smoke_windows_v292.py').read_text()
        self.assertIn('ImageGrab.grab(bbox=rect)',src)
        self.assertNotIn('ImageGrab.grab().save',src)
    def test_platform_guard(self):
        with patch('windows_window_probe_v286.sys.platform','linux'):
            with self.assertRaisesRegex(RuntimeError,'Windows required'):
                window_rectangle(123)
    def test_installer_pdf_gate_before_writes(self):
        with patch.object(installer,'run_pdf_functional',return_value={'merge':'PASS'}) as run:
            result=installer.qualify(root=ROOT)
        run.assert_called_once()
        self.assertEqual(result['checks']['pdf_engine_functional']['merge'],'PASS')
        self.assertEqual(result['status'],'FAIL')
    def test_current_build(self):
        build=(ROOT/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertRegex(build,r'openpdf_windows_v[23]\d+\.py')
        self.assertRegex(build,r'smoke_windows_v[23]\d+\.py --static')
    def test_installer_version(self):
        self.assertIn('OpenPDF-Studio-V29.2-Setup',(ROOT/'OpenPDF-Studio-V29.2.iss').read_text())
if __name__=='__main__':unittest.main()
