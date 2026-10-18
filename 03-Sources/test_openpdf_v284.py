import unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import smoke_windows_v284 as smoke

class SmokeTests(unittest.TestCase):
    def test_requires_executable(self):
        with patch.object(smoke,'ROOT',Path('/tmp/nonexistent-openpdf-v284')):
            with self.assertRaises(RuntimeError):smoke.verify_static()
    def test_no_linux_launch(self):
        if smoke.sys.platform!='win32':
            with self.assertRaises(RuntimeError):smoke.verify_launch()
    def test_script_contains_cleanup(self):
        self.assertIn('proc.terminate()',Path(smoke.__file__).read_text())
    def test_pipeline_runs_static_smoke(self):
        text=(Path(__file__).parent/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertRegex(text, r'smoke_windows_v\d+\.py --static')
    def test_inno_version(self):
        text=(Path(__file__).parent/'OpenPDF-Studio-V28.4.iss').read_text()
        self.assertIn('AppVersion',text)
        self.assertIn('28.4',text)
if __name__=='__main__':unittest.main()
