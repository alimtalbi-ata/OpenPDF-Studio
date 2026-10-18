import unittest
from visual_coordinate_transform import map_raster_region,convert_raster_regions
from visual_text_correlation import correlate_visual_text

class TransformTests(unittest.TestCase):
 def region(self,**changes):
  d=dict(side='source',page=2,coordinate_space='full_page_raster',rotation=0,raster_width=1000,raster_height=2000,pdf_width=500,pdf_height=1000,bbox=[100,200,300,400]);d.update(changes);return d
 def test_map(self):
  v=map_raster_region(self.region());self.assertEqual(v['bbox'],[50,100,150,200]);self.assertEqual(v['page'],2)
 def test_no_provenance(self):self.assertIsNone(map_raster_region(self.region(coordinate_space='viewport')))
 def test_rotation(self):self.assertIsNone(map_raster_region(self.region(rotation=90)))
 def test_outside(self):self.assertIsNone(map_raster_region(self.region(bbox=[0,0,1001,10])))
 def test_nonfinite(self):self.assertIsNone(map_raster_region(self.region(pdf_width=float('nan'))))
 def test_bool(self):self.assertIsNone(map_raster_region(self.region(page=True)))
 def test_invalid_dimensions(self):self.assertIsNone(map_raster_region(self.region(raster_height=0)))
 def test_conversion(self):self.assertEqual(len(convert_raster_regions({'visual_regions_raster_space':[self.region(),self.region(rotation=90)]})),1)
 def test_no_implicit_conversion(self):self.assertEqual(convert_raster_regions({'visual_regions':[self.region()]}),[])
 def test_correlation(self):
  mapped=convert_raster_regions({'visual_regions_raster_space':[self.region()]});r={'visual_regions_pdf_space':mapped,'page_annotations':[{'side':'source','page':2,'bbox':[50,100,150,200]}]};self.assertEqual(correlate_visual_text(r)[0]['iou'],1)
 def test_limits(self):
  with self.assertRaises(ValueError):convert_raster_regions({},0)
if __name__=='__main__':unittest.main()
