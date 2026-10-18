import unittest
from pathlib import Path
from unittest.mock import patch
from qualify_installer_v291 import qualify,existing_installations
ROOT=Path(__file__).resolve().parent
class Release290Tests(unittest.TestCase):
    def test_default_refuses_install(self):
        r=qualify(root=ROOT)
        self.assertEqual(r['status'],'FAIL')
        self.assertIn('disabled by default',r['error'])
    def test_windows_required(self):
        with patch('qualify_installer_v291.sys.platform','linux'):
            r=qualify(root=ROOT,allow_install_test=True)
        self.assertIn('Windows required',r['error'])
    def test_existing_installation_blocks_before_setup(self):
        with patch('qualify_installer_v291.sys.platform','win32'),patch('qualify_installer_v291.existing_installations',return_value=[{'location':'C:/Existing'}]):
            r=qualify(root=ROOT,allow_install_test=True)
        self.assertIn('Existing OpenPDF Studio',r['error'])
    def test_build_references_current_entry(self):
        s=(ROOT/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertRegex(s,r'openpdf_windows_v[23]\d+\.py')
        self.assertRegex(s,r'OpenPDF-Studio-V\d+\.\d+\.iss')
    def test_qualifier_requires_opt_in(self):
        s=(ROOT/'QUALIFY-INSTALLER-V29.1.cmd').read_text()
        self.assertIn('--allow-install-test',s)
if __name__=='__main__':unittest.main()
