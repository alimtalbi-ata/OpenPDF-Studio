import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from audit_dossier_v256 import create,verify
from test_bind_pdf_audit_v255 import BoundAuditTests
class DossierTests(BoundAuditTests):
 def test_dossier(self):
  out=Path(self.tmp.name)/'dossier.zip';a=Path(self.tmp.name)/'audit.json';a.write_text(json.dumps(self.audit))
  self.assertTrue(create(a,self.s,self.t,out)[0]);self.assertTrue(verify(out)[0])
 def test_tamper_pdf(self):
  out=Path(self.tmp.name)/'dossier.zip';a=Path(self.tmp.name)/'audit.json';a.write_text(json.dumps(self.audit));create(a,self.s,self.t,out)
  with zipfile.ZipFile(out) as z:content={n:z.read(n) for n in z.namelist()}
  content['source.pdf']+=b'changed'
  with zipfile.ZipFile(out,'w') as z:
   for n,data in content.items():z.writestr(n,data)
  self.assertFalse(verify(out)[0])
 def test_missing_file(self):
  out=Path(self.tmp.name)/'bad.zip'
  with zipfile.ZipFile(out,'w') as z:z.writestr('source.pdf',b'%PDF-1.4')
  self.assertFalse(verify(out)[0])
 def test_non_pdf(self):
  out=Path(self.tmp.name)/'bad.zip';a=Path(self.tmp.name)/'audit.json';a.write_text(json.dumps(self.audit));self.s.write_bytes(b'not pdf')
  with self.assertRaises(ValueError):create(a,self.s,self.t,out)
if __name__=='__main__':unittest.main()
