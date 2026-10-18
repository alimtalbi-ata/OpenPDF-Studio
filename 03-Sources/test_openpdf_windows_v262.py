import unittest
from unittest.mock import Mock
from openpdf_windows_v262 import PageEditor
class PageEditorLogicTests(unittest.TestCase):
    def make_editor(self):
        obj=PageEditor.__new__(PageEditor)
        obj.pages=[{'number':i,'rotation':0} for i in range(1,5)]
        obj.listbox=Mock();obj._redraw=Mock()
        return obj
    def test_move_up(self):
        x=self.make_editor();x.listbox.curselection.return_value=(2,);x.move(-1)
        self.assertEqual([p['number'] for p in x.pages],[1,3,2,4])
    def test_move_down(self):
        x=self.make_editor();x.listbox.curselection.return_value=(1,);x.move(1)
        self.assertEqual([p['number'] for p in x.pages],[1,3,2,4])
    def test_move_multiple(self):
        x=self.make_editor();x.listbox.curselection.return_value=(1,2);x.move(1)
        self.assertEqual([p['number'] for p in x.pages],[1,4,2,3])
    def test_rotate(self):
        x=self.make_editor();x.listbox.curselection.return_value=(0,2);x.rotate(-90)
        self.assertEqual([p['rotation'] for p in x.pages],[270,0,270,0])
    def test_delete(self):
        x=self.make_editor();x.listbox.curselection.return_value=(0,2);x.delete()
        self.assertEqual([p['number'] for p in x.pages],[2,4])
    def test_no_move_beyond_boundary(self):
        x=self.make_editor();x.listbox.curselection.return_value=(0,);x.move(-1)
        self.assertEqual([p['number'] for p in x.pages],[1,2,3,4])
if __name__=='__main__':unittest.main()
