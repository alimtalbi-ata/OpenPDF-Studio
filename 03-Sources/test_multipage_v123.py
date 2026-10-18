import unittest
from multipage_audit import audit_multipage, detect_split_merge_candidates

def p(s):return {'blocks':[{'text':s}]}
class SplitMergeTests(unittest.TestCase):
 def test_split(self):
  a=[p('alpha beta gamma delta epsilon zeta eta theta')]
  b=[p('alpha beta gamma delta'),p('epsilon zeta eta theta')]
  x=detect_split_merge_candidates(a,b)
  self.assertEqual(x[0]['type'],'split')
  self.assertEqual(x[0]['target_pages'],[1,2])
 def test_merge(self):
  a=[p('alpha beta gamma delta'),p('epsilon zeta eta theta')]
  b=[p('alpha beta gamma delta epsilon zeta eta theta')]
  self.assertEqual(detect_split_merge_candidates(a,b)[0]['type'],'merge')
 def test_empty_not_matched(self):
  self.assertEqual(detect_split_merge_candidates([p('')],[p(''),p('')]),[])
 def test_unrelated_not_matched(self):
  self.assertEqual(detect_split_merge_candidates([p('alpha beta gamma delta')],[p('x y'),p('z w')]),[])
 def test_output_integrated(self):
  self.assertIn('split_merge_candidates',audit_multipage([p('one two three four')],[p('one two'),p('three four')]))
 def test_threshold_validation(self):
  with self.assertRaises(ValueError):detect_split_merge_candidates([],[],threshold=0)
if __name__=='__main__':unittest.main()
