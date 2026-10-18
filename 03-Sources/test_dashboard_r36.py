import unittest
from diagnostic_dashboard import align_page_pairs,build_dashboard

class R36Tests(unittest.TestCase):
 def test_shifted_pages(self):
  r={'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':2}]}}
  self.assertEqual(align_page_pairs(r,{1},{1,2}),[(1,2,'exact-text'),(None,1,'unmatched-target')])
 def test_candidates_labeled(self):
  r={'multipage_audit':{'candidate_text_page_matches':[{'source_page':3,'target_page':4}]}}
  self.assertIn((3,4,'candidate-text'),align_page_pairs(r,{3},{4}))
 def test_no_guess_by_number(self):
  self.assertEqual(align_page_pairs({}, {1},{1}),[(1,None,'unmatched-source'),(None,1,'unmatched-target')])
 def test_duplicate_target_not_reused(self):
  r={'multipage_audit':{'exact_text_page_matches':[{'source_page':1,'target_page':2},{'source_page':3,'target_page':2}]}}
  pairs=align_page_pairs(r,{1,3},{2})
  self.assertEqual(pairs.count((1,2,'exact-text')),1)
  self.assertIn((3,None,'unmatched-source'),pairs)
 def test_bad_input_ignored(self):
  r={'multipage_audit':{'exact_text_page_matches':[{'source_page':True,'target_page':1},{'source_page':-1,'target_page':1},'bad']}}
  self.assertEqual(len(align_page_pairs(r,{1},{1})),2)
 def test_html_safe_and_labeled(self):
  r={'warnings':['<script>alert(1)</script>']}
  html=build_dashboard(r)
  self.assertNotIn('<script>alert(1)</script>',html)
  self.assertIn('Diagnostic V25.4',html)
if __name__=='__main__':unittest.main()
