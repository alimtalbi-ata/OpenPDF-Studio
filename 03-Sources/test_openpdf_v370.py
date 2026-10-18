import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from openpdf_lock_diagnostics import inspect_lock

class TestLockDiagnostics(unittest.TestCase):
 def test_absent(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(inspect_lock(Path(d)/"file.pdf")["status"],"absent")
 def test_invalid(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/".file.pdf.openpdf.lock").write_text("garbled")
   self.assertEqual(inspect_lock(Path(d)/"file.pdf")["status"],"unknown")
 def test_pid_never_stolen(self):
  with tempfile.TemporaryDirectory() as d:
   lock=Path(d)/".file.pdf.openpdf.lock";lock.write_text("99999999\n")
   self.assertIn(inspect_lock(Path(d)/"file.pdf")["status"],("possibly_orphaned","unverified"))
   self.assertTrue(lock.exists())
 def test_existing_process(self):
  import os
  with tempfile.TemporaryDirectory() as d:
   lock=Path(d)/".file.pdf.openpdf.lock";lock.write_text(str(os.getpid()))
   self.assertIn(inspect_lock(Path(d)/"file.pdf")["status"],("pid_exists_unverified","unverified"))
 def test_no_lock_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   lock=Path(d)/".file.pdf.openpdf.lock";lock.write_text("1234\n")
   with patch("openpdf_lock_diagnostics.os.kill",side_effect=ProcessLookupError): inspect_lock(Path(d)/"file.pdf")
   self.assertEqual(lock.read_text(),"1234\n")
if __name__=='__main__': unittest.main()
