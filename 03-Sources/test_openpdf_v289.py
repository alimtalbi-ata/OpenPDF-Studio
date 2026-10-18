import tempfile
import unittest
from pathlib import Path
from qualify_installer_v289 import is_windows_pe

class Release289Tests(unittest.TestCase):
    def test_missing_file(self):
        self.assertFalse(is_windows_pe('/not/present/installer.exe'))
    def test_mz_alone_is_insufficient(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'setup.exe';p.write_bytes(b'MZ'+b'\0'*300)
            self.assertFalse(is_windows_pe(p))
    def test_pe_signature(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'setup.exe'; b=bytearray(512);b[:2]=b'MZ';b[0x3c:0x40]=(128).to_bytes(4,'little');b[128:132]=b'PE\0\0';p.write_bytes(b)
            self.assertTrue(is_windows_pe(p))
    def test_out_of_bounds_offset(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'setup.exe';b=bytearray(512);b[:2]=b'MZ';b[0x3c:0x40]=(999999).to_bytes(4,'little');p.write_bytes(b)
            self.assertFalse(is_windows_pe(p))
    def test_build_uses_current_version(self):
        root=Path(__file__).resolve().parent
        s=(root/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
        self.assertRegex(s, r'openpdf_windows_v[23][0-9]+\.py')
        self.assertRegex(s, r'OpenPDF-Studio-V(29|30|31|32)\.[0-9]+\.iss')
if __name__=='__main__':unittest.main()
