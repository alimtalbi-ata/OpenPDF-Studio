import unittest
from pathlib import Path
from verify_release_v318 import check_source
class Release318(unittest.TestCase):
 def test_sources(self):self.assertTrue(check_source())
 def test_documentation(self):
  root=Path(__file__).parent/'Documentation'
  for sub,ext in [('Word','docx'),('PDF','pdf')]:
   self.assertGreater((root/sub/f'OpenPDF-Studio-V31.8-Manuel-Complet.{ext}').stat().st_size,10000)
 def test_capture_provenance(self):
  s=(Path(__file__).parent/'Documentation/Qualification/CAPTURES-STATUS-V31.8.md').read_text(encoding='utf-8')
  self.assertIn('non disponibles',s)
if __name__=='__main__':unittest.main()
