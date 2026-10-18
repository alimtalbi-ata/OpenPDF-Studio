"""V38.7: verified conversion digest and publication. Author Abdelhalim Talbi."""
import unittest, tempfile, sys, hashlib
from pathlib import Path
from unittest.mock import patch
import fitz
sys.path.insert(0,str(Path(__file__).parent))
from openpdf_conversion_service_v351 import convert_office
from types import SimpleNamespace
class OfficeIntegrity(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.base=Path(tmp.name);self.src=self.base/'src.pdf';self.dst=self.base/'out.docx'
  with fitz.open() as pdf:pdf.new_page();pdf.save(self.src)
 def converter(self,src,dst):Path(dst).write_bytes(b'office-demo-payload')
 def audit(self,src,dst):return SimpleNamespace(sha256=hashlib.sha256(Path(dst).read_bytes()).hexdigest(),warnings=())
 def test_digest_success(self):
  with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':self.converter}),patch('openpdf_conversion_service_v351.audit_conversion',self.audit):result=convert_office(self.src,self.dst)
  self.assertEqual(result.sha256,hashlib.sha256(self.dst.read_bytes()).hexdigest())
 def test_digest_mismatch_never_publishes(self):
  with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':self.converter}),patch('openpdf_conversion_service_v351.audit_conversion',return_value=SimpleNamespace(sha256='0'*64,warnings=())):
   with self.assertRaisesRegex(RuntimeError,'Empreinte'):convert_office(self.src,self.dst)
  self.assertFalse(self.dst.exists());self.assertFalse(list(self.base.glob('.openpdf-office-*')))
 def test_audit_failure_no_output(self):
  with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':self.converter}),patch('openpdf_conversion_service_v351.audit_conversion',side_effect=RuntimeError('audit failed')):
   with self.assertRaises(RuntimeError):convert_office(self.src,self.dst)
  self.assertFalse(self.dst.exists());self.assertFalse(list(self.base.glob('.openpdf-office-*')))
if __name__=='__main__':unittest.main()
