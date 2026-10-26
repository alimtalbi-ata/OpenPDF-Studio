"""V555 versioned-document tests. Author: Abdelhalim Talbi."""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_docs_v555_test", ROOT / "02-Compilation" / "generate_docs_v555.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class GenerateDocsV555Tests(unittest.TestCase):
    def test_docx_pdf_and_architecture_diagrams_have_exact_sha_provenance(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as temporary:
            out = GEN.generate(temporary, commit_sha=sha, pr_number=61, workflow_run_id=40360000000)
            for key in ("docx", "pdf", "png", "svg"):
                path = Path(out[key])
                self.assertTrue(path.is_file(), key)
                self.assertGreater(path.stat().st_size, 0, key)
            with zipfile.ZipFile(out["docx"]) as archive:
                self.assertIsNone(archive.testzip())
                xml = archive.read("word/document.xml").decode("utf-8")
                for expected in (sha, "V555", "Abdelhalim Talbi", "local-record"):
                    self.assertIn(expected, xml)
            import fitz
            pdf = fitz.open(out["pdf"])
            try:
                self.assertGreaterEqual(pdf.page_count, 1)
                page_text = [page.get_text() for page in pdf]
                text = "\n".join(page_text)
                for expected in (sha, "V555", "Abdelhalim Talbi", "ZIP local-record", "EOCD", "non indexés"):
                    self.assertIn(expected, text)
                trace_pages = [page for page in page_text if "Traçabilité" in page]
                self.assertTrue(trace_pages, "PDF traceability section must be present")
                self.assertTrue(
                    any("Commit:" in page for page in trace_pages),
                    "Traceability heading must stay with its provenance body",
                )
            finally:
                pdf.close()
            svg = Path(out["svg"]).read_text(encoding="utf-8")
            self.assertIn("not an application screenshot", svg)
            from PIL import Image
            with Image.open(out["png"]) as image:
                self.assertEqual(image.size, (1120, 330))

    def test_invalid_sha_is_explicitly_unqualified(self):
        context = GEN.build_context(commit_sha="not-a-sha", pr_number=61, workflow_run_id=40360000000)
        sections = dict(GEN.build_sections(context))
        self.assertEqual(context["commit_sha"], "NOT-VERIFIED")
        self.assertIn("non qualifié", sections["Traçabilité"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
