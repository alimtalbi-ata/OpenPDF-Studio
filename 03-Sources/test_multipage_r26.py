import unittest
from multipage_audit import audit_multipage

def page(s):
    return {'blocks':[{'text':s}] if s else []}

class MultipageAuditTests(unittest.TestCase):
    def test_exact(self):
        r=audit_multipage([page('alpha'),page('beta')],[page('alpha'),page('beta')]);self.assertEqual(len(r['exact_text_page_matches']),2)
    def test_insert(self):
        r=audit_multipage([page('alpha'),page('beta')],[page('alpha'),page('inserted'),page('beta')]);self.assertEqual(r['page_count_delta'],1);self.assertEqual(r['unmatched_target_pages'],[2])
    def test_empty(self):
        r=audit_multipage([page('')],[page('')]);self.assertEqual(r['empty_text_source_pages'],[1])
    def test_candidate(self):
        r=audit_multipage([page('alpha beta gamma')],[page('alpha beta delta')]);self.assertEqual(r['candidate_text_page_matches'][0]['status'],'candidate_only')
    def test_invalid(self):
        with self.assertRaises(ValueError):audit_multipage({},[])
    def test_limit(self):
        with self.assertRaises(ValueError):audit_multipage([page('a')]*1001,[])

if __name__=='__main__':unittest.main()
