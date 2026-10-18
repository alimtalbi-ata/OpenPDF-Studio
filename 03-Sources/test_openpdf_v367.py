import unittest, tempfile, multiprocessing, time
from pathlib import Path
from openpdf_reservation import reserve
from openpdf_operations import run_operation
import fitz

def holder(path, ready, release):
    with reserve(path):
        ready.set()
        release.wait(10)

class ReservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.d=Path(self.tmp.name); self.src=self.d/'input.pdf'
        with fitz.open() as pdf:
            pdf.new_page().insert_text((40,60),'reservation test')
            pdf.save(self.src)
    def test_release_after_success(self):
        target=self.d/'out.pdf'; run_operation('extraction',[self.src],target,first=1,last=1)
        self.assertTrue(target.exists());self.assertFalse((self.d/'.out.pdf.openpdf.lock').exists())
    def test_release_after_failure(self):
        bad=self.d/'bad.pdf';bad.write_bytes(b'invalid')
        with self.assertRaises(Exception):run_operation('fusion',[bad],self.d/'out.pdf')
        self.assertFalse((self.d/'.out.pdf.openpdf.lock').exists())
    def test_existing_lock_not_removed(self):
        p=self.d/'out.pdf';lock=self.d/'.out.pdf.openpdf.lock';lock.write_text('other')
        with self.assertRaises(FileExistsError):
            with reserve(p):pass
        self.assertEqual(lock.read_text(),'other')
    def test_concurrent_process_blocked(self):
        p=self.d/'out.pdf';ready=multiprocessing.Event();release=multiprocessing.Event()
        proc=multiprocessing.Process(target=holder,args=(p,ready,release));proc.start()
        try:
            self.assertTrue(ready.wait(5))
            with self.assertRaises(FileExistsError):run_operation('extraction',[self.src],p,first=1,last=1)
            self.assertFalse(p.exists())
        finally:
            release.set();proc.join(5)
            if proc.is_alive():proc.terminate();proc.join()
        self.assertEqual(proc.exitcode,0)
    def test_split_lock_cleanup(self):
        run_operation('decoupage',[self.src],self.d,chunk=1)
        self.assertFalse((self.d/'..openpdf-split.openpdf.lock').exists())
    def test_split_collision_preserves_existing(self):
        p=self.d/'input_pages_0001-0001.pdf';p.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):run_operation('decoupage',[self.src],self.d,chunk=1)
        self.assertEqual(p.read_bytes(),b'KEEP')

if __name__=='__main__':unittest.main()
