import tempfile
import unittest
from pathlib import Path
import fitz
from page_sequence_audit_v234 import audit_page_sequence

class PageSequenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
    def pdf(self, name, pages, sizes=None):
        p=Path(self.tmp.name)/name
        with fitz.open() as doc:
            for i,txt in enumerate(pages):
                page=doc.new_page(width=(sizes or [(595,842)]*len(pages))[i][0],height=(sizes or [(595,842)]*len(pages))[i][1])
                if txt:page.insert_text((50,50),txt)
            doc.save(p)
        return p
    def test_reorder_and_insert(self):
        a=self.pdf('a.pdf',['Alpha','Beta','Gamma'])
        b=self.pdf('b.pdf',['Gamma','Alpha','New','Beta'])
        r=audit_page_sequence(a,b)
        self.assertEqual(len(r['matched_pages']),3)
        self.assertEqual(r['unmatched_target_pages'],[3])
        self.assertEqual(len(r['moved_pages']),3)
    def test_deleted_page(self):
        a=self.pdf('a.pdf',['Alpha','Beta'])
        b=self.pdf('b.pdf',['Alpha'])
        self.assertEqual(audit_page_sequence(a,b)['unmatched_source_pages'],[2])
    def test_ambiguous_duplicates(self):
        a=self.pdf('a.pdf',['Same','Same'])
        b=self.pdf('b.pdf',['Same'])
        self.assertEqual(audit_page_sequence(a,b)['unmatched_source_pages'],[2])
    def test_blank_pages_not_matched(self):
        a=self.pdf('a.pdf',[''])
        b=self.pdf('b.pdf',[''])
        self.assertEqual(audit_page_sequence(a,b)['matched_pages'],[])
    def test_geometry_difference(self):
        a=self.pdf('a.pdf',['Alpha'])
        b=self.pdf('b.pdf',['Alpha'],[(612,792)])
        self.assertEqual(len(audit_page_sequence(a,b)['geometry_changes_on_exact_matches']),1)
    def test_modified_not_equivalent(self):
        a=self.pdf('a.pdf',['Alpha'])
        b=self.pdf('b.pdf',['Alphb'])
        self.assertEqual(audit_page_sequence(a,b)['matched_pages'],[])
if __name__=='__main__':unittest.main()
