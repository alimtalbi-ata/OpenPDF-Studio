"""Headless V27.7 layout regression tests. Abdelhalim Talbi."""
import unittest
from openpdf_commands_v276 import COMMANDS, Command
from openpdf_ui_layout_v277 import PANELS, unique_commands, normalize_progress

class LayoutTests(unittest.TestCase):
    def test_three_panels(self): self.assertEqual([p.key for p in PANELS], ['pages','tools','properties'])
    def test_commands_unique(self): self.assertEqual(len(unique_commands(COMMANDS)), len(COMMANDS))
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError): unique_commands((Command('a','A','foo'),Command('a','B','bar')))
    def test_progress_clamped(self): self.assertEqual([normalize_progress(v) for v in (-1,0,.5,2)], [0,0,50,100])
    def test_invalid_progress(self): self.assertEqual(normalize_progress(float('nan')),0)

if __name__=='__main__': unittest.main()
