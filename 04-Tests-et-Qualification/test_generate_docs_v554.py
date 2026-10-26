"""V554 guide generation tests; diagrams are labeled and never represented as screenshots.
Author: Abdelhalim Talbi.
"""
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_docs_v554_test", ROOT / "02-Compilation" / "generate_docs_v554.py"
)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class V554DocumentationTests(unittest.TestCase):
    def test_versioned_docx_pdf_and_diagrams_bind_exact_sha_pr_and_run(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as temporary:
            out = GENERATOR.generate(
                temporary, commit_sha=sha, pr_number=60, workflow_run_id=40345390400
            )
            for key in ("docx", "pdf", "png", "svg"):
                path = Path(out[key])
                self.assertTrue(path.is_file(), key)
                self.assertGreater(path.stat().st_size, 0, key)

            with zipfile.ZipFile(out["docx"]) as docx:
                self.assertIsNone(docx.testzip())
                xml = docx.read("word/document.xml").decode("utf-8")
                for expected in (sha, "V554", "Abdelhalim Talbi", "200:1", "100:1", "40345390400"):
                    self.assertIn(expected, xml)

            import fitz
            pdf = fitz.open(out["pdf"])
            try:
                self.assertGreaterEqual(pdf.page_count, 1)
                text = "\n".join(page.get_text() for page in pdf)
                for expected in (sha, "V554", "Abdelhalim Talbi", "200:1", "100:1", "40345390400"):
                    self.assertIn(expected, text)
            finally:
                # Windows keeps the generated PDF locked until the MuPDF handle is closed.
                pdf.close()

            svg = Path(out["svg"]).read_text(encoding="utf-8")
            self.assertIn("ZIP resource preflight", svg)
            self.assertIn("not a real application screenshot", svg)
            from PIL import Image
            with Image.open(out["png"]) as image:
                self.assertEqual(image.size, (1120, 330))

    def test_missing_exact_sha_is_explicitly_unverified(self):
        context = GENERATOR.build_context(commit_sha="not-a-sha", pr_number=60, workflow_run_id=40345390400)
        sections = dict(GENERATOR.build_sections(context))
        self.assertEqual(context["commit_sha"], "NOT-VERIFIED")
        self.assertIn("qualification non vérifiée", sections["Traçabilité CI"])
        self.assertIn("SHA n'a pas été fourni", sections["Traçabilité CI"])

    def test_guide_reports_limits_and_unqualified_proof_domains(self):
        context = GENERATOR.build_context(
            commit_sha="b" * 40, pr_number=60, workflow_run_id=40345390400
        )
        sections = dict(GENERATOR.build_sections(context))
        text = "\n".join(sections.values())
        for expected in ("200 000 membres", "8 GiB", "4 GiB", "Authenticode", "fidélité visuelle Office"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
