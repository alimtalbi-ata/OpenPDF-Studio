import ast
import unittest
from pathlib import Path
from openpdf_task_presenter_v334 import completion_view
class TestV335(unittest.TestCase):
    def test_no_global_presenter_monkeypatch(self):
        source=Path(__file__).with_name("openpdf_windows_v334.py").read_text(encoding="utf-8")
        self.assertNotIn("previous.completion_view =",source)
    def test_v335_local_presenter(self):
        source=Path(__file__).with_name("openpdf_windows_v335.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("completion_view(phase, result, self._v331_compression)",source)
    def test_cancelled(self):
        self.assertEqual(completion_view("CANCELLED",object()).kind,"cancelled")
    def test_failed(self):
        self.assertEqual(completion_view("FAILED",object()).kind,"error")
    def test_no_result(self):
        self.assertEqual(completion_view("SUCCEEDED",object()).kind,"warning")
if __name__=="__main__": unittest.main()
