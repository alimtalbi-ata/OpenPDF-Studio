import unittest
from diagnostic_dashboard import build_dashboard, collect_findings
class DashboardTests(unittest.TestCase):
 def test_empty(self):
  self.assertEqual(collect_findings({}),[])
  self.assertIn('No findings',build_dashboard({}))
 def test_warning(self):
  self.assertEqual(collect_findings({'warnings':['font substitution']})[0]['severity'],'medium')
 def test_html_escape(self):
  page=build_dashboard({'warnings':['<script>alert("x")</script>']})
  self.assertIn('&lt;script&gt;',page)
  self.assertNotIn('<script>alert',page)
 def test_layout(self):
  self.assertEqual(collect_findings({'layout_comparable':False})[0]['kind'],'layout')
 def test_tables(self):
  issues=collect_findings({'pdf_office_table_audit':{'matches':[{'source_id':'t1','missing_rows':[['x']]}]}})
  self.assertEqual(issues[0]['severity'],'high')
 def test_severity_filter_present(self):
  page=build_dashboard({'warnings':['a']})
  self.assertIn('id="severity"',page)
  self.assertIn('data-severity="medium"',page)
 def test_csv_export_present(self):
  self.assertIn('openpdf-diagnostic-v25.4.csv',build_dashboard({}))
 def test_invalid_input(self):
  with self.assertRaises(ValueError):collect_findings([])
if __name__=='__main__':unittest.main()
