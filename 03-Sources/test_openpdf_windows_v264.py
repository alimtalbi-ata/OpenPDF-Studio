import unittest
from openpdf_windows_v264 import visible_range

class VirtualGalleryTests(unittest.TestCase):
    def test_empty(self): self.assertEqual(list(visible_range(0, 500, 0)), [])
    def test_zero_viewport(self): self.assertEqual(list(visible_range(0, 0, 100)), [])
    def test_start(self): self.assertEqual(list(visible_range(0, 232, 100)), list(range(5)))
    def test_middle(self): self.assertEqual(list(visible_range(1160, 232, 100)), list(range(8, 15)))
    def test_end(self): self.assertEqual(list(visible_range(11600, 232, 102)), list(range(98, 102)))
    def test_negative_offset(self): self.assertEqual(list(visible_range(-50, 232, 100)), list(range(5)))
    def test_large_count_bounded(self): self.assertLessEqual(len(visible_range(100000, 600, 1000000)), 12)

if __name__ == '__main__': unittest.main()
