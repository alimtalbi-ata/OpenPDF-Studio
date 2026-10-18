import unittest
from report_quality import assess_report_quality
from diagnostic_dashboard import build_dashboard

class ReportQualityTests(unittest.TestCase):
    def test_empty_report_is_partial(self):
        q=assess_report_quality({},[])
        self.assertEqual(q['label'],'Couverture partielle')
        self.assertFalse(q['fully_verified'])
    def test_complete_evidence_is_not_certification(self):
        r={'layout_comparable':True,'multipage_audit':{'matches':[1]},'pdf_office_table_audit':{'matches':[1]},'page_annotations':[{'side':'source'}], 'source':{'geometry':'native_pdf'},'target':{'geometry':'libreoffice_rendered_pdf'}}
        q=assess_report_quality(r,[])
        self.assertEqual(q['label'],'Couverture documentée')
        self.assertFalse(q['fully_verified'])
    def test_high_finding_requires_review(self):
        r={'layout_comparable':True,'multipage_audit':{'x':1},'pdf_office_table_audit':{'x':1},'page_annotations':[1], 'source':{'geometry':'native_pdf'},'target':{'geometry':'native_pdf'}}
        self.assertTrue(any('validation humaine' in x for x in assess_report_quality(r,[{'severity':'high'}])['limitations']))
    def test_input_validation(self):
        with self.assertRaises(ValueError):assess_report_quality([],[])
    def test_dashboard_includes_quality(self):
        h=build_dashboard({})
        self.assertIn('Fiabilité du diagnostic',h)
        self.assertIn('V20.9',h)
    def test_html_escape(self):
        h=build_dashboard({'warnings':['<script>alert(1)</script>']})
        self.assertNotIn('<script>alert(1)</script>',h)
        self.assertIn('&lt;script&gt;',h)
if __name__=='__main__':unittest.main()
