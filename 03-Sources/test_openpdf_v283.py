import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from verify_release_v283 import check_source,check_exe,check_installer
class TestRelease(unittest.TestCase):
    def test_source(self): self.assertTrue(check_source())
    def test_missing_exe_fails(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(AssertionError):check_exe(Path(d))
    def test_missing_installer_fails(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(AssertionError):check_installer(Path(d))
    def test_exe_artifacts(self):
        with TemporaryDirectory() as d:
            root=Path(d);p=root/'dist'/'OpenPDF-Studio';(p/'_internal').mkdir(parents=True);(p/'OpenPDF-Studio.exe').write_bytes(b'MZ'+b'0'*100001)
            self.assertTrue(check_exe(root))
    def test_installer_pe_signature(self):
        with TemporaryDirectory() as d:
            root=Path(d);p=root/'dist'/'OpenPDF-Studio';(p/'_internal').mkdir(parents=True);(p/'OpenPDF-Studio.exe').write_bytes(b'MZ'+b'0'*100001)
            q=root/'installer';q.mkdir();(q/'OpenPDF-Studio-V28.3-Setup.exe').write_bytes(b'BAD'+b'0'*100001)
            with self.assertRaises(AssertionError):check_installer(root)
if __name__=='__main__':unittest.main()
