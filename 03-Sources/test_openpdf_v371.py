import unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
from openpdf_reservation import reserve,read_owner,lock_path
from openpdf_lock_diagnostics import inspect_lock
class TestReservation371(unittest.TestCase):
 def test_owner_token(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf"
   with reserve(target):
    owner=read_owner(target);self.assertEqual(owner["status"],"metadata_valid");self.assertEqual(len(owner["token"]),48)
   self.assertEqual(read_owner(target)["status"],"absent")
 def test_collision(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf"
   with reserve(target):
    with self.assertRaises(FileExistsError):
     with reserve(target):pass
 def test_legacy(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf";lock_path(target).write_text("1234\n")
   self.assertEqual(read_owner(target)["status"],"legacy_pid_only")
 def test_modified_lock_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf"
   with reserve(target):lock_path(target).write_text("999\n")
   self.assertTrue(lock_path(target).exists())
 def test_diagnostics_read_only(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf"
   with reserve(target):
    before=lock_path(target).read_bytes(); report=inspect_lock(target)
    self.assertEqual(report["owner_format"],"metadata_valid")
    self.assertEqual(before,lock_path(target).read_bytes())
 def test_remote_host_not_pid_checked(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf"
   with reserve(target):
    owner=json.loads(lock_path(target).read_text());owner["hostname"]="other-host";lock_path(target).write_text(json.dumps(owner))
    with patch("openpdf_lock_diagnostics.os.kill",side_effect=AssertionError("must not check remote pid")):
     self.assertEqual(inspect_lock(target)["status"],"remote_host_unverified")
 def test_invalid_json(self):
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/"out.pdf";lock_path(target).write_text("bad")
   self.assertEqual(inspect_lock(target)["status"],"unknown")
if __name__=="__main__":unittest.main()
