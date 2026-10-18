import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_compression_v323 import diagnose_pdf,compress_with_profile
class TestV323(unittest.TestCase):
 def test_text_pdf(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'in.pdf';out=Path(d)/'out.pdf'
   doc=fitz.open();page=doc.new_page();page.insert_text((72,72),'Test de diagnostic');doc.save(p);doc.close()
   info=diagnose_pdf(p)
   self.assertEqual(info['pages'],1);self.assertEqual(info['pages_avec_texte'],1)
   self.assertEqual(info['images'],0)
   compress_with_profile(p,out,'standard')
   self.assertTrue(out.exists())
 def test_invalid_pdf(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.pdf';p.write_bytes(b'not a pdf')
   with self.assertRaises(Exception):diagnose_pdf(p)
if __name__=='__main__':unittest.main()
