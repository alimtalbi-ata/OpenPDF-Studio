import unittest
from openpdf_workspace_v270 import WorkspaceController, ACTIONS, OPERATIONS_BY_ACTION

class WorkspaceTests(unittest.TestCase):
    def test_empty(self):
        self.assertIsNone(WorkspaceController().selected())
    def test_selection(self):
        c=WorkspaceController(); c.replace(['a.pdf','b.pdf']); self.assertEqual(c.select(1),'b.pdf'); self.assertEqual(c.selected(),'b.pdf')
    def test_invalid_selection(self):
        c=WorkspaceController(); c.replace(['a.pdf'])
        with self.assertRaises(IndexError): c.select(3)
    def test_action_registry(self):
        self.assertEqual(len(set(a.label for a in ACTIONS)),len(ACTIONS))
        self.assertEqual(set(OPERATIONS_BY_ACTION), {'_merge','_compress','_split'})
if __name__=='__main__': unittest.main()
