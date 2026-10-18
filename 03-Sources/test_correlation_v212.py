import unittest
from visual_text_correlation import correlate_visual_text

class CorrelationTests(unittest.TestCase):
 def test_overlap(self):
  r={'visual_regions_pdf_space':[{'side':'source','page':1,'bbox':[0,0,10,10]}],'page_annotations':[{'side':'source','page':1,'bbox':[5,5,15,15]}]}
  v=correlate_visual_text(r);self.assertEqual(len(v),1);self.assertEqual(v[0]['status'],'spatial_overlap_only');self.assertAlmostEqual(v[0]['iou'],0.1429,places=4)
 def test_other_page(self):
  self.assertEqual(correlate_visual_text({'visual_regions_pdf_space':[{'side':'source','page':2,'bbox':[0,0,10,10]}],'page_annotations':[{'side':'source','page':1,'bbox':[0,0,10,10]}]}),[])
 def test_other_side(self):
  self.assertEqual(correlate_visual_text({'visual_regions_pdf_space':[{'side':'target','page':1,'bbox':[0,0,10,10]}],'page_annotations':[{'side':'source','page':1,'bbox':[0,0,10,10]}]}),[])
 def test_touching_not_overlap(self):
  self.assertEqual(correlate_visual_text({'visual_regions_pdf_space':[{'side':'source','page':1,'bbox':[0,0,10,10]}],'page_annotations':[{'side':'source','page':1,'bbox':[10,0,20,10]}]}),[])
 def test_invalid_coordinates(self):
  self.assertEqual(correlate_visual_text({'visual_regions_pdf_space':[{'side':'source','page':1,'bbox':[0,0,float('nan'),10]}],'page_annotations':[{'side':'source','page':1,'bbox':[0,0,10,10]}]}),[])
 def test_no_implicit_browser_coordinates(self):
  self.assertEqual(correlate_visual_text({'visual_regions':[{'side':'source','page':1,'bbox':[0,0,10,10]}],'page_annotations':[{'side':'source','page':1,'bbox':[0,0,10,10]}]}),[])
 def test_empty_and_malformed(self):
  self.assertEqual(correlate_visual_text(None),[]);self.assertEqual(correlate_visual_text({'visual_regions_pdf_space':{}}),[])
if __name__=='__main__':unittest.main()
