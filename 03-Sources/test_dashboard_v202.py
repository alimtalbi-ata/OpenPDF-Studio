import unittest
from diagnostic_dashboard import build_dashboard

class V202(unittest.TestCase):
 def test_navigation_controls(self):
  h=build_dashboard({'warnings':['Test anomaly']})
  self.assertIn('id="issue-nav"',h)
  self.assertIn('id="go-issue"',h)
  self.assertIn('populateIssues()',h)
 def test_row_metadata(self):
  h=build_dashboard({'warnings':['Test anomaly']})
  self.assertIn('data-side=""',h)
 def test_escaping(self):
  h=build_dashboard({'warnings':['<img src=x onerror=alert(1)>']})
  self.assertIn('&lt;img',h)
  self.assertNotIn('<img src=x onerror=',h)
 def test_no_findings(self):
  self.assertIn('Aucun aperçu',build_dashboard({}))

if __name__=='__main__':unittest.main()
