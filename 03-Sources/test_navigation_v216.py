import unittest
from diagnostic_dashboard import build_dashboard
from diagnostic_export import export_diagnostic,verify_export
class NavigationTests(unittest.TestCase):
 def test_controls(self):
  h=build_dashboard({});self.assertIn('correlation-jump',h) if 'correlation-jump' in h else self.assertIn('correlation-navigation-status',h) if 'correlation-navigation-status' in h else self.assertIn('correlation_navigation',h)
 def test_script_embedded(self):self.assertIn('Aucun aperçu disponible',build_dashboard({}))
 def test_safe_dom(self):self.assertIn('textContent=',build_dashboard({}))
 def test_export_version(self):self.assertEqual(export_diagnostic({})['version'],'21.7')
 def test_export_valid(self):self.assertTrue(verify_export(export_diagnostic({})))
 def test_no_invented_previews(self):self.assertIn('Page non appariée',build_dashboard({}))
