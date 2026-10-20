"""No-gain compression short circuit: do not perform costly validation. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_v327 import compress_with_profile

class CompressionNoGainTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.pdf'
        with fitz.open() as doc:
            doc.new_page()
            doc.save(self.source)
        self.destination=self.root/'output.pdf'
    def test_no_gain_skips_quality_pipeline(self):
        def larger(source,target):
            Path(target).write_bytes(Path(source).read_bytes()+b'\n% no gain padding\n')
        with patch('openpdf_compression_v327.compress_pdf',side_effect=larger),patch('openpdf_quality_v327.assess_candidate',side_effect=AssertionError('quality must not run')):
            receipt=compress_with_profile(self.source,self.destination,'smaller_only')
        self.assertIn('Aucun gain',receipt)
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob('.openpdf-*.pdf')))
    def test_standard_still_runs_quality(self):
        def copy(source,target):Path(target).write_bytes(Path(source).read_bytes())
        with patch('openpdf_compression_v327.compress_pdf',side_effect=copy),patch('openpdf_quality_v327.assess_candidate',side_effect=RuntimeError('quality invoked')):
            with self.assertRaisesRegex(RuntimeError,'quality invoked'):
                compress_with_profile(self.source,self.destination,'standard')
        self.assertFalse(self.destination.exists())
if __name__=='__main__':unittest.main()
