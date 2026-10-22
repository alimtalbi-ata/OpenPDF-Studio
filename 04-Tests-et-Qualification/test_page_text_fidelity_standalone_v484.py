"""Standalone tests for mapped PDF text fidelity. Abdelhalim Talbi."""
import sys
import tempfile
import unittest
from pathlib import Path
import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03-Sources"))
from openpdf_page_text_fidelity_v484 import validate_page_text_fidelity

class TextFidelityTests(unittest.TestCase):
    def test_page_mapping_and_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            a = Path(directory) / "source.pdf"
            b = Path(directory) / "candidate.pdf"
            with fitz.open() as pdf:
                pdf.new_page().insert_text((40, 80), "Source content")
                pdf.new_page().insert_text((40, 80), "Second page")
                pdf.save(a)
            with fitz.open(a) as source, fitz.open() as output:
                output.insert_pdf(source, from_page=1, to_page=1)
                output.insert_pdf(source, from_page=0, to_page=0)
                output.save(b)
            result = validate_page_text_fidelity([(a, [2, 1])], b)
            self.assertEqual(result["pages_verified"], 2)
            with self.assertRaises(RuntimeError):
                validate_page_text_fidelity([(a, [1, 2])], b)

if __name__ == "__main__":
    unittest.main()
