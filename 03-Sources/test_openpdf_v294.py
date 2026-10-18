import unittest, tempfile
from pathlib import Path
from verify_release_v294 import check_source,check_portable
class TestV294(unittest.TestCase):
    def test_source(self): self.assertTrue(check_source())
    def test_portable_missing_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(AssertionError): check_portable(Path(d))
    def test_portable_invalid_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'portable';p.mkdir();(p/'OpenPDF-Studio-Portable-V29.4.exe').write_bytes(b'X'*150000)
            with self.assertRaises(AssertionError):check_portable(Path(d))
    def test_onefile(self):
        b=(Path(__file__).parent/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertIn('--onefile',b)
        self.assertIn('--onedir',b)
if __name__=='__main__':unittest.main()
