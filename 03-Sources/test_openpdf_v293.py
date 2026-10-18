import unittest
from pathlib import Path
from unittest.mock import patch
import ui_audit_v293 as ui
ROOT=Path(__file__).parent
class V293Tests(unittest.TestCase):
    def test_non_windows_fails_closed(self):
        with patch.object(ui.sys,'platform','linux'):
            self.assertEqual(ui.audit()['status'],'FAIL')
    def test_inventory_with_fake_tk(self):
        class Widget:
            def __init__(self,name,children=()):self.name=name;self.children=children
            def winfo_class(self):return 'Button'
            def __str__(self):return self.name
            def cget(self,k):return {'text':'Fusionner','state':'normal','command':'cb'}[k]
            def winfo_children(self):return self.children
        items=ui.inventory(Widget('root',[Widget('child')]))
        self.assertEqual(len(items),2);self.assertEqual(items[1]['depth'],1);self.assertTrue(items[0]['has_command'])
    def test_audit_closes_app(self):
        class App:
            closed=False
            def update_idletasks(self):pass
            def update(self):pass
            def title(self):return 'OpenPDF Studio'
            def destroy(self):self.closed=True
        app=App()
        with patch.object(ui.sys,'platform','win32'),patch.object(ui,'inventory',return_value=[{'has_command':True}]):
            report=ui.audit(lambda:app)
        self.assertEqual(report['status'],'PASS');self.assertTrue(app.closed)
    def test_audit_missing_actions_fails(self):
        with patch.object(ui.sys,'platform','win32'),patch.object(ui,'inventory',return_value=[{'class':'Frame'}]):
            report=ui.audit(lambda:type('App',(),{'update_idletasks':lambda self:None,'update':lambda self:None,'title':lambda self:'App','destroy':lambda self:None})())
        self.assertEqual(report['status'],'FAIL')
    def test_build_version(self):
        build=(ROOT/'CHANGELOG-V29.3.md').read_text() + (ROOT/'openpdf_windows_v293.py').read_text() + (ROOT/'OpenPDF-Studio-V29.3.iss').read_text()
        self.assertIn('OpenPDF Studio V29.3',build)
        self.assertIn('OutputBaseFilename=OpenPDF-Studio-V29.3-Setup',build)
    def test_ui_script(self):
        self.assertIn('ui_audit_v293.py',(ROOT/'QUALIFY-UI-V29.3.cmd').read_text())
if __name__=='__main__':unittest.main()
