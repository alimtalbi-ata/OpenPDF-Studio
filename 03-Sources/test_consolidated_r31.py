import unittest
from consolidated_table_compare import compare_consolidated_tables

def t(id,page,rows):
    return {'id':id,'page':page,'columns':2,'header':['Name','Value'],'cells':rows}
def o(id,rows):
    return {'id':id,'columns':2,'header':['Name','Value'],'cells':rows}

class TestConsolidated(unittest.TestCase):
    def setUp(self):
        self.pdf=[t('p1',1,[['Name','Value'],['A','1']]),t('p2',2,[['Name','Value'],['B','2']])]
        self.office=[o('word',[['Name','Value'],['A','1'],['B','2']])]
    def test_match_group(self):
        r=compare_consolidated_tables(self.pdf,self.office)
        self.assertEqual(r['pdf_candidate_count'],1)
        self.assertEqual(len(r['matches']),1)
        self.assertEqual(r['matches'][0]['source_table_ids'],['p1','p2'])
        self.assertEqual(r['matches'][0]['repeated_headers_excluded'],1)
        self.assertEqual(r['matches'][0]['missing_rows'],[])
    def test_missing_row(self):
        r=compare_consolidated_tables(self.pdf,[o('word',[['Name','Value'],['A','1']])],threshold=.2)
        self.assertIn(['b','2'],r['matches'][0]['missing_rows'])
    def test_order_changed(self):
        r=compare_consolidated_tables(self.pdf,[o('word',[['Name','Value'],['B','2'],['A','1']])])
        self.assertTrue(r['matches'][0]['row_order_changed_candidate'])
    def test_unmatched(self):
        r=compare_consolidated_tables(self.pdf,[],threshold=.5)
        self.assertEqual(len(r['unmatched_source']),1)
    def test_no_auto_merge_without_repeated_header(self):
        other=t('p2',2,[['Other','Field'],['B','2']]);other['header']=['Other','Field']
        r=compare_consolidated_tables([self.pdf[0],other],self.office)
        self.assertEqual(r['pdf_candidate_count'],2)
        self.assertEqual(len(r['pdf_fragment_audit']['ambiguous_adjacencies']),1)
    def test_no_mutation(self):
        import copy
        original=copy.deepcopy(self.pdf)
        compare_consolidated_tables(self.pdf,self.office)
        self.assertEqual(self.pdf,original)

if __name__=='__main__': unittest.main()
