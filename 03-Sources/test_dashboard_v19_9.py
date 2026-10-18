import unittest
from diagnostic_dashboard import split_merge_comparison_sections,build_dashboard

class SplitMergeDashboardTests(unittest.TestCase):
 def test_split(self):
  r={'multipage_audit':{'split_merge_candidates':[{'type':'split','source_pages':[1],'target_pages':[1,2],'text_overlap':.9}]}}
  html=split_merge_comparison_sections(r,{})
  self.assertIn('Division 1→2',html)
  self.assertIn('Aperçu indisponible',html)
 def test_merge(self):
  r={'multipage_audit':{'split_merge_candidates':[{'type':'merge','source_pages':[1,2],'target_pages':[1],'text_overlap':.86}]}}
  self.assertIn('Fusion 2→1',split_merge_comparison_sections(r,{}))
 def test_reject_invalid(self):
  r={'multipage_audit':{'split_merge_candidates':[{'type':'split','source_pages':[0],'target_pages':[1,2],'text_overlap':.9},{'type':'split','source_pages':[1],'target_pages':[1,2],'text_overlap':float('nan')}]}}
  self.assertEqual(split_merge_comparison_sections(r,{}),'')
 def test_dedupe(self):
  c={'type':'split','source_pages':[1],'target_pages':[1,2],'text_overlap':.9}
  self.assertEqual(split_merge_comparison_sections({'multipage_audit':{'split_merge_candidates':[c,c]}},{}).count('Division 1→2'),1)
 def test_in_report(self):
  c={'type':'split','source_pages':[1],'target_pages':[1,2],'text_overlap':.9}
  self.assertIn('Division 1→2',build_dashboard({'multipage_audit':{'split_merge_candidates':[c]}}))
 def test_escape(self):
  html=split_merge_comparison_sections({'multipage_audit':{'split_merge_candidates':[{'type':'split','source_pages':[1],'target_pages':[1,2],'text_overlap':.8}]}},{'source':{1:'data:image/png;base64,AA=='}})
  self.assertIn('data:image/png;base64,AA==',html)
if __name__=='__main__':unittest.main()
