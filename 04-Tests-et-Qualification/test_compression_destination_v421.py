"""Compression refuses existing outputs before expensive work. Abdelhalim Talbi."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_v327 import compress_with_profile

class CompressionDestinationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.src=self.root/'src.pdf'
        with fitz.open() as pdf:
            pdf.new_page().insert_text((72,72),'Protected PDF input')
            pdf.save(self.src)
    def test_existing_destination_not_processed_or_overwritten(self):
        output=self.root/'output.pdf';output.write_bytes(b'important preexisting document')
        with patch('openpdf_compression_v327.compress_pdf') as engine:
            with self.assertRaises(FileExistsError):
                compress_with_profile(str(self.src),str(output),'standard')
            engine.assert_not_called()
        self.assertEqual(output.read_bytes(),b'important preexisting document')
    def test_no_gain_does_not_mask_preexisting_destination(self):
        output=self.root/'output.pdf';output.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            compress_with_profile(str(self.src),str(output),'smaller_only')
        self.assertEqual(output.read_bytes(),b'keep')
    def test_no_staging_file_created_on_preflight_rejection(self):
        output=self.root/'output.pdf';output.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            compress_with_profile(str(self.src),str(output),'images_balanced')
        self.assertEqual(list(self.root.glob('.openpdf-*.pdf')),[])
if __name__=='__main__':unittest.main()
