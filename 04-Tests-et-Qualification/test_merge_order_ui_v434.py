"""PDF source ordering for merge UI. Abdelhalim Talbi."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import move_selected_source

class OrderingTests(unittest.TestCase):
    def test_move_up(self):
        self.assertEqual(move_selected_source(['a','b','c'],2,-1),(['a','c','b'],1))
    def test_move_down(self):
        self.assertEqual(move_selected_source(['a','b','c'],0,1),(['b','a','c'],1))
    def test_boundaries(self):
        self.assertEqual(move_selected_source(['a','b'],0,-1),(['a','b'],0))
        self.assertEqual(move_selected_source(['a','b'],1,1),(['a','b'],1))
    def test_invalid_selection(self):
        self.assertEqual(move_selected_source(['a','b'],None,1),(['a','b'],None))
    def test_invalid_direction(self):
        with self.assertRaises(ValueError):move_selected_source(['a'],0,2)
if __name__=='__main__':unittest.main()
