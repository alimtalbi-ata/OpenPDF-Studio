import tempfile
import unittest
from pathlib import Path
from openpdf_engine_v271 import PDFOperationError, _atomic_pdf, merge_pdfs, extract_pages
from openpdf_tasks_v271 import TaskRunner

class EngineTests(unittest.TestCase):
    def test_no_input(self):
        with self.assertRaises(PDFOperationError):
            merge_pdfs([], "output.pdf")

    def test_atomic_failure_preserves_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "out.pdf"
            target.write_bytes(b"original")
            def broken(path):
                Path(path).write_bytes(b"partial")
                raise RuntimeError("failure")
            with self.assertRaises(RuntimeError):
                _atomic_pdf(target, broken)
            self.assertEqual(target.read_bytes(), b"original")
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["out.pdf"])

    def test_task_error_is_captured(self):
        runner = TaskRunner(1)
        try:
            result = runner.submit(lambda: 1 / 0).result(timeout=5)
            self.assertIsInstance(result.error, ZeroDivisionError)
        finally:
            runner.shutdown()

    def test_merge_and_extract(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")
        with tempfile.TemporaryDirectory() as directory:
            a, b, merged, extracted = [Path(directory) / name for name in ('a.pdf','b.pdf','merged.pdf','extract.pdf')]
            for path in (a,b):
                with fitz.open() as doc:
                    doc.new_page()
                    doc.save(path)
            merge_pdfs([a,b], merged)
            extract_pages(merged, extracted, 2, 2)
            with fitz.open(merged) as doc: self.assertEqual(len(doc), 2)
            with fitz.open(extracted) as doc: self.assertEqual(len(doc), 1)
            with self.assertRaises(PDFOperationError): merge_pdfs([a], a)

if __name__ == '__main__': unittest.main()
