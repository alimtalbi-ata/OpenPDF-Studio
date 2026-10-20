"""Compression must never replace a destination created during processing.
Author: Abdelhalim Talbi.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_v327 import compress_with_profile

class CompressionExclusiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source.pdf'
        with fitz.open() as pdf:
            pdf.new_page().insert_text((70,70),'OpenPDF compression test')
            pdf.save(self.source)
    def test_existing_destination_preserved_on_publish_race(self):
        output=self.root/'output.pdf'
        def racing_engine(src,dst):
            with fitz.open(src) as doc:
                doc.save(dst)
            output.write_bytes(b'ANOTHER PROCESS')
        with patch('openpdf_compression_v327.compress_pdf',side_effect=racing_engine):
            with patch('openpdf_quality_v327.assess_candidate',return_value={'pages_texte_modifie':0}):
                with self.assertRaises(FileExistsError):
                    compress_with_profile(str(self.source),str(output),'standard')
        self.assertEqual(output.read_bytes(),b'ANOTHER PROCESS')
        self.assertEqual(list(self.root.glob('.openpdf-*.pdf')),[])
if __name__=='__main__':unittest.main()
