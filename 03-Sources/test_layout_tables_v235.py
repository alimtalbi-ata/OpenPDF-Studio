import tempfile
import unittest
from pathlib import Path
import fitz
from layout_table_audit_v235 import audit_layout_tables

class LayoutAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def pdf(self, name, y=70, text="Same text", empty=False):
        p = self.root/name
        with fitz.open() as d:
            page=d.new_page()
            if not empty: page.insert_text((70,y),text)
            d.save(p)
        return p

    def test_identical(self):
        a=self.pdf('a.pdf'); b=self.pdf('b.pdf')
        self.assertEqual(audit_layout_tables(a,b)['findings'],[])

    def test_shifted_block(self):
        a=self.pdf('a.pdf'); b=self.pdf('b.pdf',y=130)
        self.assertTrue(any(x['kind']=='text_block_geometry' for x in audit_layout_tables(a,b)['findings']))

    def test_tolerance(self):
        a=self.pdf('a.pdf'); b=self.pdf('b.pdf',y=72)
        self.assertEqual(audit_layout_tables(a,b,tolerance=4)['findings'],[])

    def test_unmatched_not_inferred(self):
        a=self.pdf('a.pdf'); b=self.pdf('b.pdf',text='Other text')
        result=audit_layout_tables(a,b)
        self.assertEqual(result['matched_pages_examined'],0)
        self.assertEqual(result['unmatched_source_pages'],[1])

    def test_invalid_tolerance(self):
        a=self.pdf('a.pdf'); b=self.pdf('b.pdf')
        with self.assertRaises(ValueError): audit_layout_tables(a,b,tolerance=-1)

    def test_blank_not_equivalent(self):
        a=self.pdf('a.pdf',empty=True); b=self.pdf('b.pdf',empty=True)
        self.assertEqual(audit_layout_tables(a,b)['matched_pages_examined'],0)

if __name__=='__main__': unittest.main()
