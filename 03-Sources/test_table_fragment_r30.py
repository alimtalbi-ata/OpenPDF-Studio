import unittest
from table_fragment_audit import audit_pdf_table_fragments

def t(i,p,header=('Name','Value'),rows=None,columns=2):
    rows = rows if rows is not None else [list(header),[f'item{i}',str(i)]]
    return {'id':i,'page':p,'columns':columns,'header':list(header),'cells':rows}

class TestFragments(unittest.TestCase):
    def test_repeated_header_and_dedup(self):
        result=audit_pdf_table_fragments([t('a',1),t('b',2)])
        self.assertEqual(result['groups'][0]['table_ids'],['a','b'])
        self.assertEqual(result['groups'][0]['rows'],3)
        self.assertEqual(result['groups'][0]['repeated_headers_excluded'],1)
    def test_three_pages(self):
        result=audit_pdf_table_fragments([t('c',3),t('a',1),t('b',2)])
        self.assertEqual(len(result['groups']),1)
        self.assertEqual(result['groups'][0]['pages'],[1,2,3])
    def test_non_adjacent_not_grouped(self):
        self.assertFalse(audit_pdf_table_fragments([t('a',1),t('b',3)])['groups'])
    def test_different_columns_not_grouped(self):
        self.assertFalse(audit_pdf_table_fragments([t('a',1),t('b',2,columns=3)])['groups'])
    def test_different_header_ambiguous(self):
        result=audit_pdf_table_fragments([t('a',1),t('b',2,header=('Other','Field'))])
        self.assertFalse(result['groups'])
        self.assertEqual(result['ambiguous_adjacencies'][0]['reason'],'header_not_repeated_or_different')
    def test_multiple_tables_ambiguous(self):
        result=audit_pdf_table_fragments([t('a',1),t('x',1),t('b',2)])
        self.assertFalse(result['groups'])
        self.assertEqual(result['ambiguous_adjacencies'][0]['reason'],'multiple_tables_on_page')
    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):audit_pdf_table_fragments([t('a',1),t('a',2)])
    def test_bad_threshold_rejected(self):
        with self.assertRaises(ValueError):audit_pdf_table_fragments([],min_header_similarity=float('nan'))
    def test_does_not_mutate(self):
        data=[t('a',1),t('b',2)]
        import copy
        before=copy.deepcopy(data)
        audit_pdf_table_fragments(data)
        self.assertEqual(data,before)

if __name__=='__main__':unittest.main()
