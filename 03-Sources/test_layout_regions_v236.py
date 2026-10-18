import tempfile
import unittest
from pathlib import Path
import fitz
from layout_table_audit_v235 import audit_layout_tables
from diagnostic_dashboard import collect_findings, build_dashboard

class LayoutRegionV236(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def pdf(self,name,y,text='Identical measured text'):
        path=self.root/name
        with fitz.open() as doc:
            page=doc.new_page();page.insert_text((75,y),text);doc.save(path)
        return path
    def report(self):
        a=self.pdf('source.pdf',80);b=self.pdf('target.pdf',140)
        return {'layout_table_audit_v235':audit_layout_tables(a,b)}
    def test_coordinates_both_sides(self):
        findings=collect_findings(self.report())
        regions=[f for f in findings if f['kind']=='layout_region']
        self.assertEqual({f['side'] for f in regions},{'source','target'})
        self.assertEqual(len(regions),2)
        self.assertNotEqual(regions[0]['bbox'],regions[1]['bbox'])
    def test_html_contains_measured_annotations(self):
        html=build_dashboard(self.report())
        self.assertIn('Déplacement de bloc mesuré',html)
    def test_no_geometry_when_identical(self):
        a=self.pdf('a.pdf',80);b=self.pdf('b.pdf',80)
        self.assertFalse(any(f['kind']=='layout_region' for f in collect_findings({'layout_table_audit_v235':audit_layout_tables(a,b)})))
    def test_no_regions_when_text_differs(self):
        a=self.pdf('a.pdf',80);b=self.pdf('b.pdf',140,'Other text')
        self.assertEqual(audit_layout_tables(a,b)['matched_pages_examined'],0)
    def test_invalid_bbox_ignored(self):
        report={'layout_table_audit_v235':{'findings':[{'kind':'text_block_geometry','source_page':1,'target_page':1,'regions':[{'source_bbox':[0,0,-1,4],'target_bbox':[1,2,3,4]}]}]}}
        regions=[f for f in collect_findings(report) if f['kind']=='layout_region']
        self.assertEqual(len(regions),1)
        self.assertEqual(regions[0]['side'],'target')
    def test_script_injection_escaped(self):
        report={'layout_table_audit_v235':{'findings':[{'kind':'text_block_geometry','source_page':1,'target_page':1,'regions':[{'source_bbox':[1,2,3,4],'text_excerpt':'<script>alert(1)</script>'}]}]}}
        html=build_dashboard(report)
        self.assertIn('&lt;script&gt;',html)
if __name__=='__main__': unittest.main()
