"""Source-level UI contract: every PDF operation is discoverable exactly once.
Author: Abdelhalim Talbi.
"""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "03-Sources" / "openpdf_desktop.py"
DISPATCH = ROOT / "03-Sources" / "openpdf_ui_controller_v348.py"


def assigned_constant(path, variable):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == variable for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{variable} not found")


class UINavContract(unittest.TestCase):
    def test_all_operations_visible_once(self):
        groups = assigned_constant(SOURCE, "OPERATION_GROUPS")
        supported = assigned_constant(DISPATCH, "OPERATIONS")
        visible = [key for _, keys in groups for key in keys]
        self.assertEqual(len(visible), len(set(visible)))
        self.assertEqual(set(visible), set(supported))

    def test_ui_compiles_without_opening_a_window(self):
        compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec")


if __name__ == "__main__":
    unittest.main()
