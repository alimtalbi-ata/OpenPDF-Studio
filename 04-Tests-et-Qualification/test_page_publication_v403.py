"""V40.3 regression tests: never overwrite a pre-existing or concurrent PDF.
Author: Abdelhalim Talbi.
Run: python -m unittest discover -s 04-Tests-et-Qualification -p 'test_page_publication_v403.py'
"""
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "03-Sources" / "openpdf_page_service_v345.py"
import sys
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location("openpdf_page_service_v345", SOURCE)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class PagePublicationSafetyTests(unittest.TestCase):
    def test_existing_destination_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            destination = pathlib.Path(d) / "existing.pdf"
            destination.write_bytes(b"KEEP_ORIGINAL")
            with self.assertRaises(FileExistsError):
                module._target(destination, set())
            self.assertEqual(destination.read_bytes(), b"KEEP_ORIGINAL")

    def test_race_during_publication_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            destination = pathlib.Path(d) / "race.pdf"
            def writer(tmp):
                # Valid minimal PDF created with the real engine.
                with module.fitz.open() as pdf:
                    pdf.new_page()
                    pdf.save(tmp)
                destination.write_bytes(b"OTHER_PROCESS")
            with self.assertRaises(FileExistsError):
                module._publish(destination, writer)
            self.assertEqual(destination.read_bytes(), b"OTHER_PROCESS")
            self.assertFalse(list(pathlib.Path(d).glob(".openpdf-pages-*")))

    def test_successful_publication_and_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            destination = pathlib.Path(d) / "new.pdf"
            def writer(tmp):
                with module.fitz.open() as pdf:
                    pdf.new_page()
                    pdf.save(tmp)
            path, pages, digest = module._publish(destination, writer)
            self.assertEqual(path, str(destination))
            self.assertEqual(pages, 1)
            self.assertEqual(digest, module._digest(destination))
            self.assertFalse(list(pathlib.Path(d).glob(".openpdf-pages-*")))

if __name__ == "__main__":
    unittest.main()
