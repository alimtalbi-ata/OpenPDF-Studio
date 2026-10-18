import unittest
from pathlib import Path
from verify_release_v316 import check_source
class TestV316(unittest.TestCase):
 def test_release_docs(self): self.assertTrue(check_source())
 def test_manuals(self):
  p=Path(__file__).parent/'Documentation'
  self.assertTrue((p/'Word/OpenPDF-Studio-V31.6-Manuel-Complet.docx').stat().st_size>100000)
  self.assertTrue((p/'PDF/OpenPDF-Studio-V31.6-Manuel-Complet.pdf').stat().st_size>100000)
 def test_capture_truth(self):
  s=(Path(__file__).parent/'Documentation/Qualification/CAPTURES-STATUS-V31.6.md').read_text()
  self.assertIn('Aucune capture réelle',s)
if __name__=='__main__': unittest.main()
