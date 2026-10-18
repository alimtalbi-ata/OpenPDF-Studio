import tempfile, unittest
from pathlib import Path
from openpdf_lock_stress import run_stress
from openpdf_reservation import reserve, lock_path

class TestStress(unittest.TestCase):
    def test_stress_four_workers(self):
        r=run_stress(workers=4,rounds=2,hold_seconds=.06)
        self.assertTrue(r['passed'],r)
    def test_stress_eight_workers(self):
        r=run_stress(workers=8,rounds=2,hold_seconds=.06)
        self.assertTrue(r['passed'],r)
    def test_invalid_workers(self):
        with self.assertRaises(ValueError):run_stress(workers=1)
    def test_invalid_rounds(self):
        with self.assertRaises(ValueError):run_stress(rounds=0)
    def test_lock_released(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.pdf'
            with reserve(p):self.assertTrue(lock_path(p).exists())
            self.assertFalse(lock_path(p).exists())
if __name__=='__main__':unittest.main()
