import unittest
from diagnostic_pipeline import prepare_spatial_diagnostic
from diagnostic_dashboard import build_dashboard

class PipelineTests(unittest.TestCase):
 def region(self,**kw):
  r=dict(side='source',page=1,coordinate_space='full_page_raster',rotation=0,raster_width=100,raster_height=100,pdf_width=200,pdf_height=200,bbox=[10,10,30,30]);r.update(kw);return r
 def test_map(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':[self.region()]});self.assertEqual(a['mapped_regions'][0]['bbox'],[20,20,60,60])
 def test_duplicates(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':[self.region(),self.region()]});self.assertEqual(len(a['mapped_regions']),1);self.assertEqual(a['rejections']['duplicate_region'],1)
 def test_invalid(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':[self.region(rotation=90)]});self.assertEqual(a['rejections']['invalid_or_unverifiable_geometry'],1)
 def test_limit(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':[self.region(),self.region()]},limit=1);self.assertEqual(a['rejections']['over_limit'],1)
 def test_correlation(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':[self.region()],'page_annotations':[{'side':'source','page':1,'bbox':[20,20,60,60]}]});self.assertEqual(a['correlations'][0]['iou'],1)
 def test_cross_page(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':[self.region()],'page_annotations':[{'side':'source','page':2,'bbox':[20,20,60,60]}]});self.assertEqual(a['correlations'],[])
 def test_bad_collection(self):
  a=prepare_spatial_diagnostic({'visual_regions_raster_space':'bad'});self.assertEqual(a['rejections']['invalid_raster_collection'],1)
 def test_limit_invalid(self):
  with self.assertRaises(ValueError):prepare_spatial_diagnostic({},True)
 def test_dashboard(self):
  h=build_dashboard({'visual_regions_raster_space':[self.region()]});self.assertIn('Diagnostic V25.4',h);self.assertIn('Régions raster vérifiées et converties : 1',h)
if __name__=='__main__':unittest.main()
