import unittest
from pathlib import Path
from unittest.mock import patch
import qualify_installer_v288 as q
from smoke_windows_v288 import qualify
ROOT=Path(__file__).resolve().parent
class Release288Tests(unittest.TestCase):
 def test_source_entrypoint(self): self.assertRegex((ROOT/'BUILD-WINDOWS-INSTALLER.cmd').read_text(),r'openpdf_windows_v[23][0-9]+\.py')
 def test_iss(self): self.assertIn('OpenPDF-Studio-V28.8-Setup',(ROOT/'OpenPDF-Studio-V28.8.iss').read_text())
 def test_installer_qualification_wrapper(self): self.assertIn('qualify_installer_v288.py',(ROOT/'QUALIFY-INSTALLER-V28.8.cmd').read_text())
 def test_installer_qualification_fails_closed_off_windows(self):
  with patch.object(q.sys,'platform','linux'):
   r=q.qualify();self.assertEqual(r['status'],'FAIL')
 def test_installer_qualification_fails_closed_without_exe(self):
  with patch.object(q.sys,'platform','win32'):
   r=q.qualify(installer='/no/such/setup.exe');self.assertEqual(r['status'],'FAIL')
 def test_installed_exe_override(self):
  r=qualify(exe_path='/missing/openpdf.exe');self.assertEqual(r['status'],'FAIL')
if __name__=='__main__':unittest.main()
