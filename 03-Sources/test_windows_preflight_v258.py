import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from windows_preflight_v258 import inspect_environment


class WindowsPreflightTests(unittest.TestCase):
    def test_schema(self): self.assertEqual(inspect_environment()['schema'], 'openpdf-windows-preflight-v25.8')
    def test_no_false_gui_claim(self): self.assertFalse(inspect_environment()['gui_runtime_tested'])
    def test_platform_is_reported(self): self.assertIn('platform', inspect_environment())
    def test_current_files_present(self): self.assertTrue(all(inspect_environment()['files'].values()))
    def test_missing_files_fail(self):
        with tempfile.TemporaryDirectory() as d:
            result = inspect_environment(d)
            self.assertFalse(result['ready'])
            self.assertTrue(any('absent' in x for x in result['warnings']))
    def test_missing_tkinter_fail(self):
        import windows_preflight_v258 as mod
        original = mod.importlib.util.find_spec
        with patch.object(mod.importlib.util, 'find_spec', side_effect=lambda name: None if name == 'tkinter' else original(name)):
            self.assertFalse(inspect_environment()['ready'])
    def test_json_serializable(self): json.dumps(inspect_environment())
    def test_windows_launcher_exists(self): self.assertTrue(Path(__file__).with_name('LANCER-OPENPDF-AUDIT.cmd').is_file())
    def test_launcher_no_download(self):
        text = Path(__file__).with_name('LANCER-OPENPDF-AUDIT.cmd').read_text()
        self.assertNotIn('curl ', text.lower())
        self.assertNotIn('powershell ', text.lower())

if __name__ == '__main__': unittest.main()
