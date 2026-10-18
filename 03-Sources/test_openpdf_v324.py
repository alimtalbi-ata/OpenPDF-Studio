import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_compression_v324 import compress_images,compress_with_profile,PROFILES
class TestV324(unittest.TestCase):
 def test_profile_registered(self):self.assertIn('images_balanced',PROFILES)
 def test_images_profile_preserves_pages_and_text(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';doc=fitz.open();page=doc.new_page();page.insert_text((72,72),'Bonjour vectoriel');doc.save(a);doc.close()
   compress_images(a,b)
   with fitz.open(b) as check:self.assertEqual(len(check),1);self.assertIn('Bonjour',check[0].get_text())
 def test_invalid_image_parameters(self):
  with self.assertRaises(ValueError):compress_images('missing.pdf','out.pdf',dpi_target=50)
 def test_no_source_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';doc=fitz.open();doc.new_page();doc.save(a);doc.close()
   with self.assertRaises(ValueError):compress_with_profile(a,a,'images_balanced')
if __name__=='__main__':unittest.main()
