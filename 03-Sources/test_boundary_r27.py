import unittest
from boundary_audit import audit_page_boundaries


def page(*lines):
    return {'width':600,'height':800,'blocks':[{'text':x} for x in lines]}

class BoundaryAuditTests(unittest.TestCase):
    def test_hyphen(self):
        x=audit_page_boundaries([page('inter-'),page('national')])
        self.assertIn('hyphenated_word_continuation',x['boundary_candidates'][0]['reasons'])
    def test_table_candidate(self):
        x=audit_page_boundaries([page('alpha | 123'),page('beta | 456')])
        self.assertIn('possible_table_row_continuation',x['boundary_candidates'][0]['reasons'])
    def test_no_false_positive(self):
        self.assertEqual([],audit_page_boundaries([page('End.'),page('New heading')])['boundary_candidates'])
    def test_empty(self):
        self.assertEqual([],audit_page_boundaries([page(),page('Hi')])['boundary_candidates'])
    def test_limit(self):
        with self.assertRaises(ValueError):audit_page_boundaries([page()]*1001)
    def test_invalid_block(self):
        with self.assertRaises(ValueError):audit_page_boundaries([{'blocks':[{'text':4}]},page('Hi')])

if __name__=='__main__':unittest.main()
