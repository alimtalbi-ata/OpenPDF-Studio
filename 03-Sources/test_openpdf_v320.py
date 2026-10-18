import unittest,tempfile
from pathlib import Path
from unittest.mock import Mock,patch
from openpdf_compression_v320 import format_bytes,compression_with_report,guided_compress
class V320Tests(unittest.TestCase):
 def test_bytes(self):
  self.assertEqual(format_bytes(500),'500 octets')
  self.assertIn('Kio',format_bytes(2048))
 def test_report_reduction_and_growth(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'a'*100)
   for payload,expected in [(b'b'*50,'Gain'),(b'b'*150,'Augmentation'),(b'b'*100,'identique')]:
    def fake(s,d):Path(d).write_bytes(payload)
    with patch('openpdf_compression_v320.compress_pdf',side_effect=fake):
     self.assertIn(expected,compression_with_report(a,b))
 def test_dispatch(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'pdf')
   app=Mock();app.busy=False;app._v272_busy=False
   self.assertTrue(guided_compress(app,ask_source=lambda:str(a),ask_destination=lambda _:str(b)))
   self.assertEqual(app._run_pdf.call_args.args[0],compression_with_report)
if __name__=='__main__':unittest.main()
