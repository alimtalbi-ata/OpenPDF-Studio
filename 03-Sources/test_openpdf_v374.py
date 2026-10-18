import unittest, tempfile, json, os, socket
from pathlib import Path
from unittest.mock import patch
from openpdf_reservation import lock_path, inspect_orphan, recover_orphan, reserve
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.dest=Path(self.t.name)/"result.pdf"
 def create(self,pid=99999999,hostname=None):
  lock_path(self.dest).write_text(json.dumps({"schema":2,"pid":pid,"token":"a"*48,"hostname":hostname or socket.gethostname(),"created_at":1}))
 def test_absent(self): self.assertEqual(inspect_orphan(self.dest)["status"],"absent")
 def test_confirmation(self):
  self.create()
  with self.assertRaises(PermissionError):recover_orphan(self.dest)
 def test_recovery(self):
  self.create()
  with patch("openpdf_reservation.os.kill",side_effect=ProcessLookupError):
   self.assertEqual(recover_orphan(self.dest,confirm=True)["status"],"recovered")
  self.assertFalse(lock_path(self.dest).exists())
 def test_live_owner(self):
  self.create(pid=os.getpid())
  with self.assertRaises(PermissionError):recover_orphan(self.dest,confirm=True)
 def test_remote_owner(self):
  self.create(hostname="other-host")
  with self.assertRaises(PermissionError):recover_orphan(self.dest,confirm=True)
 def test_legacy_refused(self):
  lock_path(self.dest).write_text("12345")
  with self.assertRaises(PermissionError):recover_orphan(self.dest,confirm=True)
 def test_regular_reservation(self):
  with reserve(self.dest): self.assertTrue(lock_path(self.dest).exists())
  self.assertFalse(lock_path(self.dest).exists())
if __name__=="__main__":unittest.main()
