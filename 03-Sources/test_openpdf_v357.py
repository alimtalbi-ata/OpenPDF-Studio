import tempfile,unittest,sys
from pathlib import Path
import fitz
from openpdf_corpus_v357 import build_corpus
from openpdf_quality_metrics_v356 import compare_structure
class CorpusTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.cases=build_corpus(self.root)
 def test_four_cases(self):self.assertEqual(len(self.cases),4)
 def test_manifest(self):self.assertTrue((self.root/'MANIFEST-SYNTHETIC.json').is_file())
 def test_table_vectors(self):
  with fitz.open(self.root/'04-complex-table.pdf') as p:self.assertGreater(len(p[0].get_drawings()),5)
 def test_image(self):
  with fitz.open(self.root/'05-embedded-image.pdf') as p:self.assertGreater(len(p[0].get_images()),0)
 def test_multilingual_text(self):
  with fitz.open(self.root/'06-multilingual.pdf') as p:self.assertIn('English',p[0].get_text())
 def test_multipage(self):
  with fitz.open(self.root/'07-long-document.pdf') as p:self.assertEqual(p.page_count,9)
 def test_identical_metrics(self):
  p=self.root/'04-complex-table.pdf';m=compare_structure(p,p);self.assertEqual(m.page_delta,0);self.assertEqual(m.word_recall,1.0)
if __name__=='__main__':unittest.main()
