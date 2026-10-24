"""Reject a source changed while compression is running. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_v327 import compress_with_profile

class SourceChangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.pdf'
        with fitz.open() as doc:
            doc.new_page()
            doc.save(self.source)
        self.destination=self.root/'output.pdf'
    def test_modified_source_rejected_before_publication(self):
        def edit_source(source,target):
            Path(target).write_bytes(Path(source).read_bytes())
            with open(source,'ab') as stream:stream.write(b'\n% concurrent edit')
        with patch('openpdf_compression_v327.compress_pdf',side_effect=edit_source),patch('openpdf_quality_v327.assess_candidate',return_value={'pages_texte_modifie':[]} ),patch('openpdf_compression_quality_v422.validate_lossless_images',return_value={}),patch('openpdf_render_quality_v425.validate_rendered_pages',return_value={}):
            with self.assertRaisesRegex(RuntimeError,'Source modifiée'):
                compress_with_profile(self.source,self.destination,'standard')
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob('.openpdf-*.pdf')))
if __name__=='__main__':unittest.main()
