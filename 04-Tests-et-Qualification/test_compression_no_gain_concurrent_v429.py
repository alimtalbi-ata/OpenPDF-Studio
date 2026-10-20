"""Source change must not be disguised as a no-gain result. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_v327 import compress_with_profile

class NoGainConcurrentEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.pdf'
        with fitz.open() as doc:
            doc.new_page()
            doc.save(self.source)
        self.destination=self.root/'output.pdf'
    def test_source_edit_is_not_reported_as_no_gain(self):
        def edit(source,target):
            Path(target).write_bytes(Path(source).read_bytes()+b'\n% padding' * 4)
            with open(source,'ab') as stream:stream.write(b'\n% concurrent change')
        with patch('openpdf_compression_v327.compress_pdf',side_effect=edit):
            with self.assertRaisesRegex(RuntimeError,'Source modifiée'):
                compress_with_profile(self.source,self.destination,'smaller_only')
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob('.openpdf-*.pdf')))
    def test_stable_source_keeps_no_gain_fast_path(self):
        def larger(source,target):
            Path(target).write_bytes(Path(source).read_bytes()+b'\n% padding')
        with patch('openpdf_compression_v327.compress_pdf',side_effect=larger),patch('openpdf_quality_v327.assess_candidate',side_effect=AssertionError('must skip')):
            result=compress_with_profile(self.source,self.destination,'smaller_only')
        self.assertIn('Aucun gain',result)
        self.assertFalse(self.destination.exists())
if __name__=='__main__':unittest.main()
