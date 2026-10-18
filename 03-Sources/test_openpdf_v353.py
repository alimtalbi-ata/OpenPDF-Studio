import unittest,tempfile
from pathlib import Path
from docx import Document
from openpdf_fidelity_corpus_v353 import build_synthetic_corpus,pdf_metrics,benchmark_case,write_report
class CorpusTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.files=build_synthetic_corpus(self.root/'corpus')
 def tearDown(self):self.t.cleanup()
 def test_three_cases(self):self.assertEqual(len(self.files),3)
 def test_multipage(self):self.assertEqual(pdf_metrics(self.files[1]).pages,2)
 def test_vectors(self):self.assertGreater(pdf_metrics(self.files[2]).vector_drawings,0)
 def test_benchmark(self):
  output=self.root/'test.docx';d=Document();d.add_paragraph('Titre exemple Alpha beta gamma delta');d.save(output)
  case=benchmark_case(self.files[0],output);self.assertEqual(case['text_coverage']['coverage'],1.0);self.assertEqual(len(case['limits']),2)
 def test_missing_output(self):
  with self.assertRaises(FileNotFoundError):benchmark_case(self.files[0],self.root/'missing.docx')
 def test_report(self):
  p=write_report([{'test':True}],self.root/'report.json');self.assertIn('SYNTHETIQUE',p.read_text())
if __name__=='__main__':unittest.main()
