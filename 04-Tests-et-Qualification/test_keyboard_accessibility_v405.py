"""V40.5 keyboard accessibility contracts. Author: Abdelhalim Talbi."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'03-Sources'/'openpdf_desktop.py').read_text(encoding='utf-8')
class KeyboardAccessibilityTests(unittest.TestCase):
    def test_valid_python(self): ast.parse(SOURCE)
    def test_keyboard_destination(self):
        self.assertIn("'<F6>'",SOURCE)
        self.assertIn("'<Control-l>'",SOURCE)
        self.assertIn("'<Control-Shift-O>'",SOURCE)
    def test_delete_selected_files(self):
        self.assertIn("self.files.bind('<Delete>'",SOURCE)
        self.assertIn("self._remove() if not self.busy",SOURCE)
    def test_run_shortcut(self):
        self.assertIn("'<Control-Return>'",SOURCE)
if __name__=='__main__': unittest.main()
