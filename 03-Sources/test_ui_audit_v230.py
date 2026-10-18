import unittest
from ui_audit import audit_html
from diagnostic_dashboard import build_dashboard
class UIAuditTests(unittest.TestCase):
 def test_empty_document(self):self.assertFalse(audit_html('')['passed'])
 def test_duplicate_ids(self):self.assertIn('Duplicate id: x',audit_html('<html lang="fr"><title>T</title><div id="x"></div><div id="x"></div>')['issues'])
 def test_broken_anchor(self):self.assertIn('Broken anchor: #absent',audit_html('<html lang="fr"><title>T</title><a href="#absent">go</a>')['issues'])
 def test_unlabelled_control(self):self.assertIn('Unlabelled control: input#x',audit_html('<html lang="fr"><title>T</title><input id="x">')['issues'])
 def test_valid_label(self):self.assertTrue(audit_html('<html lang="fr"><title>T</title><label for="x">A</label><input id="x">')['passed'])
 def test_generated_has_version(self):self.assertIn('V25.4',build_dashboard({}))
 def test_scope(self):self.assertIn('not browser',audit_html('')['scope'])
