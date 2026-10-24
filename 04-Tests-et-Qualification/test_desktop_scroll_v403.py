"""V40.3 desktop layout contract checks (headless). Author: Abdelhalim Talbi."""
import ast
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "03-Sources" / "openpdf_desktop.py").read_text(encoding="utf-8")


class DesktopScrollContractTests(unittest.TestCase):
    def test_desktop_python_parses(self):
        ast.parse(SOURCE)

    def test_form_scrolls_and_resizes(self):
        self.assertIn("yscrollcommand=scrollbar.set", SOURCE)
        self.assertIn("scrollregion=canvas.bbox('all')", SOURCE)
        self.assertIn("canvas.itemconfigure(window_id,width=event.width)", SOURCE)
        self.assertIn("bind_wheel(left)", SOURCE)
        self.assertIn("canvas.bbox('all')[3] <= canvas.winfo_height()", SOURCE)
        self.assertLess(SOURCE.index("footer=ttk.Frame(left_host"), SOURCE.index("scroll_host=ttk.Frame(left_host"))
        self.assertLess(SOURCE.index("self.progress=ttk.Progressbar(left_host"), SOURCE.index("scroll_host=ttk.Frame(left_host"))

    def test_actions_stay_outside_scrollable_form(self):
        self.assertIn("self.go=ttk.Button(footer,", SOURCE)
        self.assertIn("self.recover_button=ttk.Button(footer,", SOURCE)
        self.assertIn("self.progress=ttk.Progressbar(left_host,", SOURCE)

    def test_destination_validation_focus(self):
        self.assertIn("if 'destination' in str(exc).lower() or 'dossier' in str(exc).lower():", SOURCE)
        self.assertIn("self._focus_destination()", SOURCE)

    def test_destination_is_reachable_from_fixed_footer(self):
        self.assertIn("command=self._focus_destination", SOURCE)
        self.assertIn("self._form_canvas.yview_moveto(1.0)", SOURCE)
        self.assertIn("self.destination_entry.focus_set()", SOURCE)
        self.assertIn("'<Control-l>'", SOURCE)

    def test_conversion_destinations(self):
        self.assertIn("asksaveasfilename", SOURCE)
        for extension in ("'docx':'.docx'", "'xlsx':'.xlsx'", "'pptx':'.pptx'"):
            self.assertIn(extension, SOURCE)


if __name__ == "__main__":
    unittest.main()
