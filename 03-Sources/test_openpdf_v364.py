import unittest, tempfile, json
from pathlib import Path
from openpdf_runtime_audit import trace_imports,save_report
from openpdf_dependency_audit import audit_directory

class RuntimeAuditTests(unittest.TestCase):
    def test_runtime_services(self):
        r=trace_imports();self.assertFalse(r['errors'],r['errors']);self.assertEqual(len(r['loaded']),4)
    def test_invalid_name_rejected(self):
        r=trace_imports(['os','openpdf_not_existing_zz']);self.assertIn('os',r['errors']);self.assertIn('openpdf_not_existing_zz',r['errors'])
    def test_string_rejected(self):
        with self.assertRaises(TypeError):trace_imports('openpdf_jobs')
    def test_json_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=save_report(trace_imports(['openpdf_jobs']),Path(d)/'audit.json')
            self.assertIn('openpdf_jobs',json.loads(p.read_text())['loaded'])
    def test_static_audit(self):
        r=audit_directory(Path(__file__).parent);self.assertGreater(r['modules'],100)
    def test_canonical_entrypoint(self):
        text=(Path(__file__).parent/'openpdf_studio.py').read_text()
        self.assertIn('openpdf_desktop',text)
    def test_ui_uses_stable_facades(self):
        text=(Path(__file__).parent/'openpdf_desktop.py').read_text()
        for module in ('openpdf_operations','openpdf_navigation','openpdf_jobs'):self.assertIn(module,text)
if __name__=='__main__':unittest.main()
