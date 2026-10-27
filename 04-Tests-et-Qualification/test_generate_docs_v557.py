"""V557 versioned Word/PDF and diagram generation tests. Author: Abdelhalim Talbi."""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_docs_v557_test", ROOT / "02-Compilation" / "generate_docs_v557.py"
)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class GenerateDocsV557Tests(unittest.TestCase):
    def test_docx_pdf_and_diagrams_include_exact_sha_and_limits(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as temporary:
            out = GEN.generate(temporary, commit_sha=sha, pr_number=63)
            for key in ("docx", "pdf", "png", "svg"):
                path = Path(out[key])
                self.assertTrue(path.is_file(), key)
                self.assertGreater(path.stat().st_size, 0, key)
            with zipfile.ZipFile(out["docx"]) as archive:
                self.assertIsNone(archive.testzip())
                xml = archive.read("word/document.xml").decode("utf-8")
                for expected in (sha, "V557", "Abdelhalim Talbi", "dupliquées", "NaN", "Traçabilité"):
                    self.assertIn(expected, xml)
            import fitz
            pdf = fitz.open(out["pdf"])
            try:
                self.assertGreaterEqual(pdf.page_count, 1)
                text = "\n".join(page.get_text() for page in pdf)
                for expected in (sha, "V557", "Abdelhalim Talbi", "dupliquées", "NaN", "Traçabilité"):
                    self.assertIn(expected, text)
                trace_pages = [page.get_text() for page in pdf if "Traçabilité" in page.get_text()]
                self.assertTrue(trace_pages, "PDF traceability section must be present")
                self.assertTrue(any("Commit:" in page for page in trace_pages))
            finally:
                pdf.close()
            svg = Path(out["svg"]).read_text(encoding="utf-8")
            self.assertIn("not an application screenshot", svg)
            self.assertIn("V556 same descriptor", svg)
            from PIL import Image
            with Image.open(out["png"]) as image:
                self.assertEqual(image.size, (1120, 360))

    def test_invalid_sha_is_explicitly_unqualified(self):
        context = GEN.build_context(commit_sha="not-a-sha", pr_number=63)
        sections = dict(GEN.build_sections(context))
        self.assertEqual(context["commit_sha"], "NOT-VERIFIED")
        self.assertIn("non qualifié", sections["Traçabilité"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
