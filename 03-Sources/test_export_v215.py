import unittest
from diagnostic_export import export_diagnostic,verify_export
from diagnostic_dashboard import build_dashboard

class ExportTests(unittest.TestCase):
    def test_empty(self):
        e=export_diagnostic({});self.assertTrue(verify_export(e));self.assertEqual(e['mapped_regions'],[])
    def test_determinism(self):
        self.assertEqual(export_diagnostic({}),export_diagnostic({}))
    def test_tampering(self):
        e=export_diagnostic({});e['version']='evil';self.assertFalse(verify_export(e))
    def test_provenance(self):
        e=export_diagnostic({'visual_regions_raster_space':[{'bbox':[0,0,1,1]}]});self.assertTrue(e['requires_human_review']);self.assertEqual(len(e['mapped_regions']),0)
    def test_schema(self):
        e=export_diagnostic({});self.assertEqual(e['schema'],'openpdf.spatial-diagnostic.v1')
    def test_html_export(self):
        h=build_dashboard({});self.assertIn('export-json',h);self.assertIn('openpdf-diagnostic-v25.3.json',h)
    def test_html_version(self):
        self.assertIn('Diagnostic V25.4',build_dashboard({}))
    def test_xss_safe(self):
        h=build_dashboard({'evil':'</script><script>alert(1)</script>'});self.assertNotIn('alert(1)',h)
