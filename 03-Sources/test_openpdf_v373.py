import unittest, tempfile, multiprocessing, os
from pathlib import Path
from openpdf_os_lock import os_lock,LockBusy
from openpdf_reservation import reserve,read_owner

def competitor(path,queue):
    try:
        with os_lock(path): queue.put("acquired")
    except LockBusy: queue.put("busy")

class OSLockTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"result.pdf"
    def test_acquire(self):
        with os_lock(self.path): self.assertTrue(True)
    def test_release_and_reacquire(self):
        with os_lock(self.path): pass
        with os_lock(self.path): pass
    def test_contention_other_process(self):
        q=multiprocessing.Queue()
        with os_lock(self.path):
            p=multiprocessing.Process(target=competitor,args=(self.path,q));p.start();p.join(8)
            self.assertEqual(p.exitcode,0);self.assertEqual(q.get(timeout=2),"busy")
    def test_release_after_exception(self):
        with self.assertRaises(ValueError):
            with os_lock(self.path): raise ValueError()
        with os_lock(self.path): pass
    def test_reservation_compatibility(self):
        with reserve(self.path): self.assertEqual(read_owner(self.path)["status"],"metadata_valid")
        self.assertEqual(read_owner(self.path)["status"],"absent")
    def test_persistent_sidecar(self):
        with os_lock(self.path): pass
        self.assertTrue((self.path.parent/("."+self.path.name+".openpdf.oslock")).exists())
if __name__=="__main__": unittest.main()
