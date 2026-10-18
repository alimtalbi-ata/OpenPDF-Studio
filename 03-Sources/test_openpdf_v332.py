import tempfile, unittest
from pathlib import Path
from openpdf_quality_dashboard_v332 import validate_output
class Tests(unittest.TestCase):
 def test_valid(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a.pdf";b=Path(d)/"b.pdf";a.write_bytes(b"123456789");b.write_bytes(b"123")
   self.assertGreater(validate_output(a,b)["gain_pct"],0)
 def test_missing(self):
  with self.assertRaises(FileNotFoundError):validate_output("absent","missing")
 def test_same(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"a.pdf";p.write_bytes(b"abc")
   with self.assertRaises(ValueError):validate_output(p,p)
 def test_empty(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a.pdf";b=Path(d)/"b.pdf";a.write_bytes(b"abc");b.touch()
   with self.assertRaises(ValueError):validate_output(a,b)
if __name__=="__main__":unittest.main()
