"""Regression: never overwrite Office output during conversion. Abdelhalim Talbi."""
import unittest,tempfile,sys,zipfile
from pathlib import Path
from unittest.mock import patch
import fitz
sys.path.insert(0,str(Path(__file__).resolve().parent))
from openpdf_conversion_service_v351 import convert_office

class ConversionSafety(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
  self.d=Path(self.temp.name); self.source=self.d/'in.pdf'; self.target=self.d/'out.docx'
  with fitz.open() as doc:
   doc.new_page().insert_text((72,72),'Test de conversion'); doc.save(self.source)
 def converter(self,src,dst):
  with zipfile.ZipFile(dst,'w') as z:z.writestr('word/document.xml','<w:document/>')
 def audit(self,src,dst):
  from types import SimpleNamespace
  return SimpleNamespace(sha256=__import__('hashlib').sha256(Path(dst).read_bytes()).hexdigest(),warnings=())
 def test_existing_destination_unchanged(self):
  self.target.write_bytes(b'original')
  with self.assertRaises(FileExistsError):convert_office(self.source,self.target)
  self.assertEqual(self.target.read_bytes(),b'original')
 def test_new_destination(self):
  with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':self.converter}),patch('openpdf_conversion_service_v351.audit_conversion',self.audit):
   out=convert_office(self.source,self.target)
  self.assertTrue(self.target.is_file());self.assertEqual(out.output_format,'docx')
 def test_race_destination_created_before_publication(self):
  def racing(src,dst):
   self.converter(src,dst);self.target.write_bytes(b'other-writer')
  with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':racing}),patch('openpdf_conversion_service_v351.audit_conversion',self.audit):
   with self.assertRaises(FileExistsError):convert_office(self.source,self.target)
  self.assertEqual(self.target.read_bytes(),b'other-writer')
  self.assertFalse(list(self.d.glob('.openpdf-office-*')))
 def test_failed_converter_cleans_temp(self):
  def broken(src,dst):raise RuntimeError('converter failed')
  with patch('openpdf_conversion_controller_v301.CONVERTERS',{'docx':broken}):
   with self.assertRaises(RuntimeError):convert_office(self.source,self.target)
  self.assertFalse(self.target.exists());self.assertFalse(list(self.d.glob('.openpdf-office-*')))
 def test_reject_bad_format(self):
  with self.assertRaises(ValueError):convert_office(self.source,self.d/'out.txt')

if __name__=='__main__':unittest.main()
