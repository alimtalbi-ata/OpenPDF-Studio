"""V548 regression tests for symlink/junction ancestors on PDF source paths.

The tests distinguish a lexical path preflight from runtime Windows
qualification. Author: Abdelhalim Talbi.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))

import openpdf_operations
import openpdf_page_service_v345 as page_service
from openpdf_source_path_guard_v548 import guard_pdf_source_path


class SourcePathChainGuardV548Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.real_dir = self.root / "real"
        self.real_dir.mkdir()
        self.source = self.real_dir / "source.pdf"
        self.chunks = self.root / "chunks"
        self.chunks.mkdir()
        with fitz.open() as document:
            document.new_page().insert_text((72, 72), "V548 safe source")
            document.save(self.source)
        self.source_sha256 = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def _synthetic_parent_link(self, candidate_parent):
        original = Path.is_symlink

        def is_link(path):
            if path == candidate_parent:
                return True
            return original(path)

        return is_link

    def test_parent_component_is_rejected_before_any_resolve(self):
        parent = self.root / "synthetic-link-dir"
        alias = parent / self.source.name
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=self._synthetic_parent_link(parent)), \
             patch.object(Path, "resolve",
                          side_effect=AssertionError("resolve must not precede path-chain rejection")):
            with self.assertRaisesRegex(ValueError, "lien symbolique"):
                guard_pdf_source_path(alias)

    def test_dotdot_cannot_hide_a_linked_parent_component(self):
        parent = self.root / "synthetic-link-dir"
        alias = parent / ".." / "real" / self.source.name
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=self._synthetic_parent_link(parent)), \
             patch.object(Path, "resolve",
                          side_effect=AssertionError("resolve must not precede path-chain rejection")):
            with self.assertRaisesRegex(ValueError, "lien symbolique"):
                guard_pdf_source_path(alias)

    def test_dispatcher_rejects_parent_alias_for_pdf_and_office_operations(self):
        parent = self.root / "synthetic-link-dir"
        alias = parent / self.source.name
        requests = (
            ("compression", self.root / "compressed.pdf", {"profile": "smaller_only"}),
            ("fusion", self.root / "merged.pdf", {}),
            ("extraction", self.root / "extracted.pdf", {}),
            ("decoupage", self.chunks, {"chunk": 1}),
            ("reorganisation", self.root / "reordered.pdf", {}),
            ("docx", self.root / "converted.docx", {}),
            ("xlsx", self.root / "converted.xlsx", {}),
            ("pptx", self.root / "converted.pptx", {}),
        )
        for operation, destination, kwargs in requests:
            with self.subTest(operation=operation):
                with patch.object(Path, "is_symlink", autospec=True,
                                  side_effect=self._synthetic_parent_link(parent)), \
                     patch.object(Path, "resolve",
                                  side_effect=AssertionError("source path was normalized before guard")):
                    with self.assertRaisesRegex(ValueError, "lien symbolique"):
                        openpdf_operations.run_operation(operation, [alias], destination, **kwargs)

        for output in ("compressed.pdf", "merged.pdf", "extracted.pdf", "reordered.pdf",
                       "converted.docx", "converted.xlsx", "converted.pptx"):
            self.assertFalse((self.root / output).exists())
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_page_service_rejects_parent_alias_for_all_page_operations(self):
        parent = self.root / "synthetic-link-dir"
        alias = parent / self.source.name
        requests = (
            lambda: page_service.merge([alias], self.root / "merged.pdf"),
            lambda: page_service.extract(alias, self.root / "extracted.pdf", 1, 1),
            lambda: page_service.reorder(alias, self.root / "reordered.pdf", [1]),
            lambda: page_service.split(alias, self.chunks, 1),
        )
        for action in requests:
            with self.subTest(action=action):
                with patch.object(Path, "is_symlink", autospec=True,
                                  side_effect=self._synthetic_parent_link(parent)), \
                     patch.object(Path, "resolve",
                                  side_effect=AssertionError("source path was normalized before guard")):
                    with self.assertRaisesRegex(ValueError, "lien symbolique"):
                        action()
        for output in ("merged.pdf", "extracted.pdf", "reordered.pdf"):
            self.assertFalse((self.root / output).exists())
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_real_parent_symlink_is_rejected_when_supported(self):
        alias_parent = self.root / "real-parent-link"
        try:
            alias_parent.symlink_to(self.real_dir, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest("Directory symlink creation unavailable: " + type(exc).__name__)
        alias = alias_parent / self.source.name
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            guard_pdf_source_path(alias)
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            openpdf_operations.run_operation("decoupage", [alias], self.chunks, chunk=1)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_sha256)
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_regular_pdf_is_accepted_without_resolving_aliases(self):
        checked = guard_pdf_source_path(self.source)
        self.assertEqual(checked, self.source)
        self.assertTrue(checked.is_file())
        self.assertEqual(checked.suffix, ".pdf")

    def test_non_pdf_and_missing_sources_fail_closed(self):
        wrong_extension = self.real_dir / "notes.txt"
        wrong_extension.write_text("not a PDF", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Source PDF invalide"):
            guard_pdf_source_path(wrong_extension)
        with self.assertRaisesRegex(ValueError, "inaccessible ou introuvable"):
            guard_pdf_source_path(self.real_dir / "missing.pdf")


if __name__ == "__main__":
    unittest.main()
