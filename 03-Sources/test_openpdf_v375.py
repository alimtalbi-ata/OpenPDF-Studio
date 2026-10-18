"""Concurrency and recovery tests; Abdelhalim Talbi."""
import multiprocessing as mp
import tempfile,unittest,os,json,socket
from pathlib import Path
from openpdf_reservation import reserve,lock_path,recover_orphan,inspect_orphan
from openpdf_os_lock import LockBusy

def contender(path, queue):
    try:
        with reserve(path): queue.put("acquired")
    except FileExistsError: queue.put("busy")

class TestReservation(unittest.TestCase):
    def test_cross_process_contention(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file.pdf"
            with reserve(p):
                q=mp.Queue(); child=mp.Process(target=contender,args=(str(p),q));child.start();child.join(10)
                self.assertEqual(child.exitcode,0);self.assertEqual(q.get(timeout=2),"busy")
            q=mp.Queue();child=mp.Process(target=contender,args=(str(p),q));child.start();child.join(10)
            self.assertEqual(q.get(timeout=2),"acquired")
    def test_crash_then_recover(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file.pdf"
            child=mp.Process(target=self._crash,args=(str(p),));child.start();child.join(10)
            self.assertEqual(child.exitcode,73)
            self.assertEqual(inspect_orphan(p)["status"],"pid_absent")
            self.assertEqual(recover_orphan(p,confirm=True)["status"],"recovered")
            with reserve(p):pass
    @staticmethod
    def _crash(path):
        with reserve(path): os._exit(73)
    def test_active_owner_protected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file.pdf"
            with reserve(p):
                with self.assertRaises((PermissionError,FileExistsError,LockBusy)): recover_orphan(p,confirm=True)
    def test_recovery_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):recover_orphan(Path(td)/"file.pdf")
    def test_remote_owner_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file.pdf";lock_path(p).write_text(json.dumps({"schema":2,"pid":999999999,"token":"a"*48,"hostname":"other-machine","created_at":1}))
            with self.assertRaises(PermissionError):recover_orphan(p,confirm=True)
    def test_legacy_owner_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file.pdf";lock_path(p).write_text("99999999")
            with self.assertRaises(PermissionError):recover_orphan(p,confirm=True)
if __name__=="__main__":unittest.main()
