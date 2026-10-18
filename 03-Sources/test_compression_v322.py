import unittest
from unittest.mock import patch,MagicMock
from openpdf_compression_v322 import PROFILES,compress_with_profile,guided_compress
class CompressionV322Tests(unittest.TestCase):
 def test_profiles(self):
  self.assertEqual(set(PROFILES),{'standard','smaller_only'})
 def test_cancel_profile(self):
  app=MagicMock();app.busy=False;app._v272_busy=False
  with patch('openpdf_compression_v322.validate_compression',return_value=('a.pdf','b.pdf')):
   self.assertFalse(guided_compress(app,ask_source=lambda:'a.pdf',ask_destination=lambda n:'b.pdf',choose_profile=lambda:None))
   app._run_pdf.assert_not_called()
 def test_invalid_profile(self):
  app=MagicMock();app.busy=False;app._v272_busy=False
  warn=MagicMock()
  with patch('openpdf_compression_v322.validate_compression',return_value=('a.pdf','b.pdf')):
   self.assertFalse(guided_compress(app,ask_source=lambda:'a.pdf',ask_destination=lambda n:'b.pdf',choose_profile=lambda:'wrong',warn=warn))
   warn.assert_called_once()
if __name__=='__main__':unittest.main()
