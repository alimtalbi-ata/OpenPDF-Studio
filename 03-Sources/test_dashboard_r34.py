import base64,io,tempfile,unittest
from pathlib import Path
from diagnostic_dashboard import collect_findings,build_dashboard

class R34Tests(unittest.TestCase):
 def test_valid_annotation(self):
  f=collect_findings({'page_annotations':[{'side':'source','page':1,'bbox':[40,40,180,75],'summary':'Test'}]})
  self.assertEqual(f[0]['bbox'],(40,40,180,75))
 def test_reject_bad_annotations(self):
  bad=[[1,2,3],[3,2,1,4],[-1,0,10,10],[0,0,float('nan'),4]]
  self.assertEqual(collect_findings({'page_annotations':[{'side':'source','page':1,'bbox':b} for b in bad]}),[])
 def test_real_highlight_changes_png(self):
  import fitz
  from PIL import Image
  with tempfile.TemporaryDirectory() as tmp:
   pdf=Path(tmp)/'a.pdf';doc=fitz.open();page=doc.new_page();page.insert_text((50,50),'hello');doc.save(pdf);doc.close()
   report={'page_annotations':[{'side':'source','page':1,'bbox':[40,35,150,60]}]}
   marked=build_dashboard(report,source_pdf=pdf)
   plain=build_dashboard({'multipage_audit':{'unmatched_source_pages':[1]}},source_pdf=pdf)
   def png(html):return base64.b64decode(html.split('data:image/png;base64,')[1].split('"')[0])
   self.assertNotEqual(png(marked),png(plain))
   im=Image.open(io.BytesIO(png(marked))).convert('RGB')
   self.assertTrue(any(r>150 and g<110 and b<110 for r,g,b in im.getdata()))
 def test_no_coordinates_no_fake_highlight(self):
  self.assertNotIn('data:image/png;base64,',build_dashboard({'page_annotations':[{'side':'source','page':1,'bbox':[0,0,10,10]}]}))
 def test_escape_summary(self):
  self.assertIn('&lt;script&gt;',build_dashboard({'page_annotations':[{'side':'source','page':1,'bbox':[1,1,2,2],'summary':'<script>'}]}))
if __name__=='__main__':unittest.main()
