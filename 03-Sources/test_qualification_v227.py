import unittest
from diagnostic_dashboard import build_dashboard
class QualificationOverviewTests(unittest.TestCase):
 def test_summary_present(self):
  html=build_dashboard({})
  self.assertIn('qualification-overview',html)
  self.assertIn('qualification-summary',html)
 def test_export_control(self):
  self.assertIn('qualification-export',build_dashboard({}))
 def test_safe_empty(self):
  self.assertIn('Aucune donnée déclarée',build_dashboard({}))
 def test_review_required(self):
  self.assertIn('review_required:true',build_dashboard({}))
 def test_no_placeholder(self):
  self.assertNotIn('__QUALIFICATION_OVERVIEW__',build_dashboard({}))
if __name__=='__main__':unittest.main()
