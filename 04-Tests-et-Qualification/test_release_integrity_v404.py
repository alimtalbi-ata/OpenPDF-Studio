"""V40.4 cumulative package integrity contract. Author: Abdelhalim Talbi."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / '02-Compilation' / 'PACKAGE-CUMULATIVE.ps1').read_text(encoding='utf-8')

class ReleaseIntegrityTests(unittest.TestCase):
    def test_integrity_inventory_and_zip_validation(self):
        for expected in ('RELEASE-FILES-SHA256.json', 'Get-FileHash', 'ZipFile]::OpenRead', 'Integrity inventory missing from ZIP'):
            self.assertIn(expected, SCRIPT)
    def test_required_release_folders(self):
        for folder in ('01-Application', '02-Compilation', '03-Sources', '04-Tests-et-Qualification', '05-Documentation', '06-Historique', '07-Manifestes'):
            self.assertIn(folder, SCRIPT)
    def test_temp_fallback(self):
        self.assertIn('[System.IO.Path]::GetTempPath()', SCRIPT)

if __name__ == '__main__':
    unittest.main()
