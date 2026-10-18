import unittest, tempfile
from pathlib import Path
from diagnostic_dashboard import build_dashboard, collect_findings

class NavigationTests(unittest.TestCase):
 def test_actual_multipage_schema(self):
  findings=collect_findings({'multipage_audit':{'unmatched_source_pages':[2], 'empty_text_target_pages':[3]}})
  self.assertEqual([(x['side'],x['page']) for x in findings],[('source',2),('target',3)])
 def test_invalid_page_ignored(self):
  self.assertEqual(collect_findings({'multipage_audit':{'unmatched_source_pages':['<script>',0,1001]}}),[])
 def test_no_preview_does_not_invent_link(self):
  html=build_dashboard({'multipage_audit':{'unmatched_source_pages':[1]}})
  self.assertIn('aperçu indisponible',html)
  self.assertNotIn('href="#preview-source-1"',html)
 def test_real_pdf_preview(self):
  import fitz
  with tempfile.TemporaryDirectory() as temp:
   pdf=Path(temp)/'sample.pdf'
   doc=fitz.open(); page=doc.new_page();page.insert_text((50,50),'Test PDF R33');doc.save(pdf);doc.close()
   html=build_dashboard({'multipage_audit':{'unmatched_source_pages':[1]}},source_pdf=pdf)
   self.assertIn('href="#preview-source-1"',html)
   self.assertIn('data:image/png;base64,',html)
   self.assertIn('Rendu réel de la page PDF',html)
 def test_non_pdf_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   file=Path(temp)/'bad.txt';file.write_text('not pdf')
   with self.assertRaises(ValueError):build_dashboard({'multipage_audit':{'unmatched_source_pages':[1]}},source_pdf=file)
 def test_existing_xss_escaped(self):
  self.assertIn('&lt;script&gt;',build_dashboard({'warnings':['<script>']}))
if __name__=='__main__':unittest.main()
