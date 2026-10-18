import unittest
from openpdf_quality_dashboard_v359 import summarize,markdown
class TestDashboard(unittest.TestCase):
 def test_pass_does_not_invent_quality(self):
  x=summarize({"results":[{"source":"a.pdf","format":"docx","status":"PASS","evidence":{}}]})
  self.assertIsNone(x[0]["visual_mae"])
 def test_failed_conversion(self):
  x=summarize({"results":[{"source":"a.pdf","format":"xlsx","status":"FAIL","error":"no converter"}]})
  self.assertEqual(x[0]["execution"],"FAIL")
  self.assertIn("N/A",markdown(x))
 def test_measured_metrics(self):
  x=summarize({"results":[{"source":"a.pdf","format":"pptx","status":"PASS","evidence":{"visual":{"mean_absolute_error":0.12},"structure":{"word_recall":0.9,"page_delta":1}}}]})
  self.assertEqual(x[0]["page_delta"],1)
if __name__=="__main__":unittest.main()
