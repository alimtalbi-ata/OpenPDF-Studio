"""V547 regression tests: reject PDF source symlinks before canonicalization.
Author: Abdelhalim Talbi.
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


class PdfSourceSymlinkGuardV547(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source.pdf"
        self.chunks = self.root / "chunks"
        self.chunks.mkdir()
        with fitz.open() as document:
            for number in range(1, 4):
                document.new_page().insert_text((72, 72), f"V547 source page {number}")
            document.save(self.source)

    def _guard_alias_before_resolve(self, alias, action):
        original_is_symlink = Path.is_symlink

        def is_alias_or_real_link(candidate):
            if candidate == alias:
                return True
            return original_is_symlink(candidate)

        # Prove ordering: a correct guard rejects the lexical alias without
        # calling resolve(), which follows the link and loses the alias.
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=is_alias_or_real_link), \
             patch.object(Path, "resolve", autospec=True,
                          side_effect=AssertionError("resolve called before symlink rejection")):
            with self.assertRaisesRegex(ValueError, "lien symbolique"):
                action()

    def test_page_service_entry_points_reject_alias_before_resolving(self):
        alias = self.root / "source-alias.pdf"
        requests = (
            ("fusion", lambda: page_service.merge([alias], self.root / "merged.pdf")),
            ("extraction", lambda: page_service.extract(alias, self.root / "extracted.pdf", 1, 2)),
            ("reorganisation", lambda: page_service.reorder(alias, self.root / "reordered.pdf", [3, 1])),
            ("decoupage", lambda: page_service.split(alias, self.chunks, 1)),
        )
        for name, action in requests:
            with self.subTest(operation=name):
                self._guard_alias_before_resolve(alias, action)

        for name in ("merged.pdf", "extracted.pdf", "reordered.pdf"):
            self.assertFalse((self.root / name).exists())
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_dispatcher_rejects_alias_before_normalizing_any_pdf_operation(self):
        alias = self.root / "source-alias.pdf"
        requests = (
            ("compression", self.root / "compressed.pdf", {"profile": "smaller_only"}),
            ("fusion", self.root / "merged.pdf", {}),
            ("extraction", self.root / "extracted.pdf", {}),
            ("decoupage", self.chunks, {"chunk": 1}),
            ("reorganisation", self.root / "reordered.pdf", {}),
        )
        with patch.object(openpdf_operations, "_legacy_run_operation") as legacy, \
             patch.object(openpdf_operations, "split_transaction") as split_tx:
            for operation, destination, kwargs in requests:
                with self.subTest(operation=operation):
                    self._guard_alias_before_resolve(
                        alias,
                        lambda operation=operation, destination=destination, kwargs=kwargs:
                            openpdf_operations.run_operation(operation, [alias], destination, **kwargs),
                    )
            legacy.assert_not_called()
            split_tx.assert_not_called()

        for name in ("compressed.pdf", "merged.pdf", "extracted.pdf", "reordered.pdf"):
            self.assertFalse((self.root / name).exists())
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_real_filesystem_symlink_is_rejected_when_supported(self):
        alias = self.root / "real-source-link.pdf"
        try:
            alias.symlink_to(self.source)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Filesystem symlink creation unavailable: {type(exc).__name__}")

        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            page_service._source(alias)
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            openpdf_operations.run_operation("decoupage", [alias], self.chunks, chunk=1)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), before)
        self.assertEqual(list(self.chunks.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
