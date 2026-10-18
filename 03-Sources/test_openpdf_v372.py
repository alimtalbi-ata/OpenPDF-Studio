import os, tempfile, unittest, json
from pathlib import Path
from unittest.mock import patch
from openpdf_reservation import reserve, lock_path, read_owner

class Reservation372(unittest.TestCase):
 def test_replacement_same_token_is_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   t=Path(d)/"x.pdf"
   with reserve(t):
    lp=lock_path(t); original=lp.read_bytes(); backup=Path(d)/"old-lock-inode";os.link(lp,backup); lp.unlink(); lp.write_bytes(original)
   self.assertTrue(lp.exists())
 def test_original_lock_released(self):
  with tempfile.TemporaryDirectory() as d:
   t=Path(d)/"x.pdf"
   with reserve(t): self.assertTrue(lock_path(t).exists())
   self.assertFalse(lock_path(t).exists())
 def test_changed_token_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   t=Path(d)/"x.pdf"
   with reserve(t):
    lp=lock_path(t); obj=json.loads(lp.read_text());obj["token"]="f"*48;lp.write_text(json.dumps(obj))
   self.assertTrue(lp.exists())
 def test_competing_process(self):
  import multiprocessing
  with tempfile.TemporaryDirectory() as d:
   t=Path(d)/"x.pdf"
   with reserve(t):
    with self.assertRaises(FileExistsError):
     with reserve(t):pass
 def test_invalid_lock_is_not_deleted(self):
  with tempfile.TemporaryDirectory() as d:
   t=Path(d)/"x.pdf"
   with reserve(t): lock_path(t).write_text("invalid")
   self.assertTrue(lock_path(t).exists())
if __name__=="__main__":unittest.main()
