"""Static regression checks for the V40.3 scrollable desktop form.

These checks verify the layout contract without requiring a Windows display.
They do not replace visual testing on a real Windows desktop.
Author: Abdelhalim Talbi.
"""
import ast
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "03-Sources" / "openpdf_desktop.py").read_text(encoding="utf-8")


def test_desktop_python_parses():
    ast.parse(SOURCE)


def test_form_is_scrollable_and_resizes():
    assert "yscrollcommand=scrollbar.set" in SOURCE
    assert "scrollregion=canvas.bbox('all')" in SOURCE
    assert "canvas.itemconfigure(window_id,width=event.width)" in SOURCE
    assert "bind_wheel(left)" in SOURCE


def test_actions_are_outside_scrollable_form():
    assert "self.go=ttk.Button(footer," in SOURCE
    assert "self.recover_button=ttk.Button(footer," in SOURCE
    assert "self.progress=ttk.Progressbar(left_host," in SOURCE


def test_conversion_destination_dialog_remains_available():
    assert "asksaveasfilename" in SOURCE
    assert "'docx':'.docx'" in SOURCE
    assert "'xlsx':'.xlsx'" in SOURCE
    assert "'pptx':'.pptx'" in SOURCE
