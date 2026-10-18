"""Regression: split rollback must not delete unrelated replacement content.
Author: Abdelhalim Talbi.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03-Sources"))
import fitz
import openpdf_page_service_v345 as service


class SplitRollbackTests(unittest.TestCase):
    def test_failed_second_chunk_keeps_replaced_first_output(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            source = directory / "source.pdf"
            with fitz.open() as pdf:
                pdf.new_page()
                pdf.new_page()
                pdf.save(source)
            first = directory / "source_pages_0001-0001.pdf"
            original_extract = service.extract
            calls = [0]

            def injected_extract(*args, **kwargs):
                calls[0] += 1
                if calls[0] == 2:
                    first.write_bytes(b"REPLACED_BY_ANOTHER_PROCESS")
                    raise RuntimeError("simulated second-chunk failure")
                return original_extract(*args, **kwargs)

            with patch.object(service, "extract", side_effect=injected_extract):
                with self.assertRaisesRegex(RuntimeError, "simulated"):
                    service.split(source, directory, 1)
            self.assertEqual(first.read_bytes(), b"REPLACED_BY_ANOTHER_PROCESS")

    def test_failed_second_chunk_removes_unchanged_first_output(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            source = directory / "source.pdf"
            with fitz.open() as pdf:
                pdf.new_page()
                pdf.new_page()
                pdf.save(source)
            first = directory / "source_pages_0001-0001.pdf"
            original_extract = service.extract
            calls = [0]

            def injected_extract(*args, **kwargs):
                calls[0] += 1
                if calls[0] == 2:
                    raise RuntimeError("simulated second-chunk failure")
                return original_extract(*args, **kwargs)

            with patch.object(service, "extract", side_effect=injected_extract):
                with self.assertRaises(RuntimeError):
                    service.split(source, directory, 1)
            self.assertFalse(first.exists())


if __name__ == "__main__":
    unittest.main()
