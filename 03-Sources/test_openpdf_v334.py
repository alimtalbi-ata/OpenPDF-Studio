import unittest, tempfile
from pathlib import Path
from types import SimpleNamespace as S
from openpdf_task_presenter_v334 import completion_view as f
class Tests(unittest.TestCase):
 def test_failed(self): self.assertEqual(f(S(name="FAILED"),S(error="bad")).kind,"error")
 def test_cancelled(self): self.assertEqual(f(S(name="CANCELLED"),S()).kind,"cancelled")
 def test_no_result(self): self.assertEqual(f(S(name="SUCCEEDED"),S(value=None)).kind,"warning")
 def test_invalid_compression(self): self.assertEqual(f(S(name="SUCCEEDED"),S(value="ok"),("/absent1","/absent2")).kind,"warning")
 def test_valid_compression(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/"a.pdf",Path(d)/"b.pdf";a.write_bytes(b"source");b.write_bytes(b"result")
   self.assertEqual(f(S(name="SUCCEEDED"),S(value="ok"),(a,b)).kind,"compression")
 def test_same_path(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/"a.pdf";a.write_bytes(b"x")
   self.assertEqual(f(S(name="SUCCEEDED"),S(value="ok"),(a,a)).kind,"error")
if __name__=="__main__": unittest.main()
