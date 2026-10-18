import unittest,tempfile,json,hashlib
from pathlib import Path
from unittest.mock import patch
from openpdf_bind_smoke import bind
from openpdf_release_gate import validate, VERSION
class ReleaseBindingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.exe=self.root/f'OpenPDF-Studio-Portable-V{VERSION}.exe';self.exe.write_bytes(b'MZdummy')
  self.report=self.root/'windows-smoke-portable.json'
  self.report.write_text(json.dumps({'version':VERSION,'mode':'portable','passed':True,'checks':[{'passed':True},{'passed':True}]}))
 def test_bind_and_gate(self):
  with patch('openpdf_bind_smoke.verify',return_value=True),patch('openpdf_release_gate.verify',return_value=True):
   bind(self.root,'portable');self.assertTrue(validate(self.root,'portable')['qualified'])
 def test_tamper_rejected(self):
  with patch('openpdf_bind_smoke.verify',return_value=True),patch('openpdf_release_gate.verify',return_value=True):
   bind(self.root,'portable');self.exe.write_bytes(b'MZchanged')
   with self.assertRaises(RuntimeError):validate(self.root,'portable')
 def test_missing_report_rejected(self):
  self.report.unlink()
  with patch('openpdf_bind_smoke.verify',return_value=True):
   with self.assertRaises(FileNotFoundError):bind(self.root,'portable')
if __name__=='__main__':unittest.main()
