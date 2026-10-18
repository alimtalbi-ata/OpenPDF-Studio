import unittest
from openpdf_windows_v263 import reorder_pages
class ReorderTests(unittest.TestCase):
    def test_single_to_end(self):
        self.assertEqual(reorder_pages([1,2,3,4],[0],4),([2,3,4,1],[3]))
    def test_group_preserves_order(self):
        self.assertEqual(reorder_pages([1,2,3,4,5],[1,3],5),([1,3,5,2,4],[3,4]))
    def test_move_to_start(self):
        self.assertEqual(reorder_pages([1,2,3],[2],0),([3,1,2],[0]))
    def test_no_selection(self):
        self.assertEqual(reorder_pages([1,2],[],1),([1,2],[]))
    def test_invalid_index(self):
        self.assertEqual(reorder_pages([1,2],[5],1),([1,2],[]))
    def test_invalid_target(self):
        with self.assertRaises(ValueError):reorder_pages([1,2],[0],3)
    def test_drop_within_selection(self):
        self.assertEqual(reorder_pages([1,2,3],[1],2),([1,2,3],[1]))
if __name__=='__main__':unittest.main()
