import unittest
from pathlib import Path
from openpdf_desktop import explain_error
class V384(unittest.TestCase):
 def test_existing(self): self.assertIn('autre nom',explain_error('Destination existante : a.pdf'))
 def test_permission(self): self.assertIn('permissions',explain_error('Permission denied'))
 def test_missing(self): self.assertIn('source',explain_error('No such file'))
 def test_fallback(self): self.assertIn('Détail technique',explain_error('Erreur inconnue'))
 def test_busy_guard(self):
  src=(Path(__file__).parent/'openpdf_desktop.py').read_text()
  self.assertIn('self.protocol("WM_DELETE_WINDOW",self._on_close)',src)
  self.assertIn('self._set_busy(True)',src)
  self.assertIn('self._set_busy(False)',src)
if __name__=='__main__': unittest.main()
