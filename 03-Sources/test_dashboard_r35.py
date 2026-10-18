import tempfile, unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard

class R35Tests(unittest.TestCase):
 def test_empty(self):
  result=build_dashboard({})
  self.assertIn('Aucun aperçu',result)
  self.assertIn('showPair(0)',result)
 def test_side_by_side_real_pdfs(self):
  import fitz
  with tempfile.TemporaryDirectory() as tmp:
   paths=[]
   for name in ('source','target'):
    p=Path(tmp)/(name+'.pdf')
    doc=fitz.open();doc.new_page().insert_text((40,40),name);doc.save(p);doc.close();paths.append(p)
   report={'page_annotations':[{'side':'source','page':1,'bbox':[30,30,100,60]},{'side':'target','page':1,'bbox':[30,30,100,60]}]}
   output=build_dashboard(report,source_pdf=paths[0],target_pdf=paths[1])
   self.assertIn('compare-grid',output)
   self.assertIn('id="preview-source-1"',output)
   self.assertIn('id="preview-target-1"',output)
   self.assertEqual(output.count('data:image/png;base64,'),2)
 def test_one_side_only(self):
  import fitz
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'s.pdf';d=fitz.open();d.new_page();d.save(p);d.close()
   result=build_dashboard({'multipage_audit':{'unmatched_source_pages':[1]}},source_pdf=p)
   self.assertIn('Aperçu indisponible',result)
   self.assertIn('id="preview-source-1"',result)
 def test_escaping(self):
  result=build_dashboard({'warnings':['<img src=x onerror=alert(1)>']})
  self.assertNotIn('<img src=x onerror=alert(1)>',result)
if __name__=='__main__':unittest.main()
