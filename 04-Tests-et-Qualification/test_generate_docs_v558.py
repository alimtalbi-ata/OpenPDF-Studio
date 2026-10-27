"""V558 documentation asset and provenance regression tests.
Author: Abdelhalim Talbi.
"""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_docs_v558_test", ROOT / "02-Compilation" / "generate_docs_v558.py"
)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class GenerateDocsV558Tests(unittest.TestCase):
    def test_docx_pdf_and_architecture_diagrams_include_exact_sha(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as temporary:
            out = GEN.generate(temporary, commit_sha=sha, pr_number=64, workflow_run_id=12345)
            for key in ("docx", "pdf", "png", "svg"):
                path = Path(out[key])
                self.assertTrue(path.is_file(), key)
                self.assertGreater(path.stat().st_size, 0, key)

            with zipfile.ZipFile(out["docx"]) as archive:
                self.assertIsNone(archive.testzip())
                xml = archive.read("word/document.xml").decode("utf-8")
                for expected in (sha, "V558", "Abdelhalim Talbi", "Precision / rappel texte",
                                 "non attestes", "Traceabilite"):
                    self.assertIn(expected, xml)
                self.assertTrue(any(name.startswith("word/media/") for name in archive.namelist()))

            import fitz
            pdf = fitz.open(out["pdf"])
            try:
                self.assertGreaterEqual(pdf.page_count, 2)
                text = "\n".join(page.get_text() for page in pdf)
                for expected in (sha, "V558", "Abdelhalim Talbi", "Precision / rappel texte",
                                 "non attestes", "Traceabilite"):
                    self.assertIn(expected, text)
                self.assertIn("https://github.com/alimtalbi-ata/OpenPDF-Studio/pull/64", text)
                self.assertIn("https://github.com/alimtalbi-ata/OpenPDF-Studio/actions/runs/12345", text)
            finally:
                pdf.close()

            svg = Path(out["svg"]).read_text(encoding="utf-8")
            self.assertIn("not an application screenshot", svg)
            self.assertIn("declared renderer provenance is not independently attested", svg)
            from PIL import Image
            with Image.open(out["png"]) as image:
                self.assertEqual(image.size, (1200, 420))
                self.assertEqual(image.format, "PNG")

    def test_invalid_sha_is_explicitly_unqualified(self):
        context = GEN.build_context(commit_sha="not-a-sha", pr_number=64)
        sections = dict(GEN.build_sections(context))
        self.assertEqual(context["commit_sha"], "NOT-VERIFIED")
        self.assertIn("explicitement non qualifie", sections["Traceabilite"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
