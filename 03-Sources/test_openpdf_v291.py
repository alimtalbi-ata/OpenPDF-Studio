import unittest
from pathlib import Path
from unittest.mock import patch
import qualify_installer_v291 as module
ROOT=Path(__file__).resolve().parent
class V291Tests(unittest.TestCase):
    def test_requires_opt_in(self):
        self.assertEqual(module.qualify(root=ROOT)['status'],'FAIL')
    def test_refuses_non_windows(self):
        with patch.object(module.sys,'platform','linux'):
            self.assertIn('Windows required',module.qualify(root=ROOT,allow_install_test=True)['error'])
    def test_refuses_existing_install(self):
        with patch.object(module.sys,'platform','win32'),patch.object(module,'existing_installations',return_value=[{'location':'existing'}]):
            self.assertIn('Existing OpenPDF Studio',module.qualify(root=ROOT,allow_install_test=True)['error'])
    def test_current_build_entry(self):
        build=(ROOT/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertRegex(build, r'openpdf_windows_v[23]\d+\.py')
        self.assertRegex(build,r'OpenPDF-Studio-V\d+\.\d+\.iss')
    def test_current_installer_qualification(self):
        script=(ROOT/'QUALIFY-INSTALLER-V29.1.cmd').read_text()
        self.assertIn('--allow-install-test',script)
        self.assertIn('qualify_installer_v291.py',script)
    def test_cleanup_failure_is_fatal(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp:
            root=Path(temp);setup=root/'setup.exe';setup.write_bytes(b'MZ')
            installed=root/'Application';installed.mkdir();(installed/'unins000.exe').write_bytes(b'MZ');(installed/'OpenPDF-Studio.exe').write_bytes(b'MZ')
            def run(executable,*args,**kwargs):
                if str(executable).endswith('unins000.exe'):raise RuntimeError('uninstall failed')
                return 0
            with patch.object(module.sys,'platform','win32'),patch.object(module,'existing_installations',return_value=[]),patch.object(module,'is_windows_pe',return_value=True),patch.object(module.tempfile,'mkdtemp',return_value=str(root)),patch.object(module,'command',side_effect=run),patch.object(module,'verify_launch',return_value=True):
                result=module.qualify(installer=setup,root=ROOT,allow_install_test=True)
            self.assertEqual(result['status'],'FAIL')
            self.assertIn('cleanup_error',result)
            self.assertTrue(result['checks']['leftover_executable'])
if __name__=='__main__':unittest.main()
