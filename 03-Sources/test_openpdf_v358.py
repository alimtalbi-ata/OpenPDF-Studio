import unittest,tempfile
from pathlib import Path
from openpdf_batch_quality_v358 import run_batch,save_report,markdown_summary
class TestBatch(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'a.pdf').write_bytes(b'%PDF fake');(self.root/'b.pdf').write_bytes(b'%PDF fake')
 def test_matrix(self):
  r=run_batch(self.root,runner=lambda p,**kw:{'ok':True});self.assertEqual((r['cases'],r['passed'],r['failed']),(6,6,0))
 def test_failure_is_recorded(self):
  def bad(*a,**kw):raise RuntimeError('failed')
  r=run_batch(self.root,formats=('docx',),runner=bad);self.assertEqual(r['failed'],2);self.assertEqual(r['results'][0]['error_type'],'RuntimeError')
 def test_unknown_format(self):
  with self.assertRaises(ValueError):run_batch(self.root,formats=('odt',))
 def test_missing_corpus(self):
  with self.assertRaises(ValueError):run_batch(self.root/'missing')
 def test_empty_corpus(self):
  (self.root/'a.pdf').unlink();(self.root/'b.pdf').unlink()
  with self.assertRaises(ValueError):run_batch(self.root)
 def test_json_and_markdown(self):
  r=run_batch(self.root,formats=('xlsx',),runner=lambda p,**kw:{'ok':True});path=save_report(r,self.root/'report.json');self.assertTrue(path.is_file());self.assertIn('| a.pdf | xlsx | PASS |',markdown_summary(r))
if __name__=='__main__':unittest.main()
