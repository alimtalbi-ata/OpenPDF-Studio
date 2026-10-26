"""V549 regression tests for linked output paths and preservation.

Tests exercise lexical preflight and public dispatcher/page-service paths. They
do not claim to eliminate races after validation. Author: Abdelhalim Talbi.
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
from openpdf_destination_path_guard_v549 import guard_destination_path


class DestinationPathChainGuardV549Tests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.real_dir = self.root / "real"
        self.real_dir.mkdir()
        self.source = self.real_dir / "source.pdf"
        with fitz.open() as document:
            document.new_page().insert_text((72, 72), "V549 safe destination test")
            document.save(self.source)
        self.source_sha256 = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.chunks = self.root / "chunks"
        self.chunks.mkdir()

    def _synthetic_parent_link(self, linked_parent):
        original = Path.is_symlink

        def is_link(path):
            if path == linked_parent:
                return True
            return original(path)

        return is_link

    def test_parent_link_is_rejected_before_any_resolve(self):
        linked_parent = self.root / "synthetic-link"
        candidate = linked_parent / "output.pdf"
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=self._synthetic_parent_link(linked_parent)), patch.object(
                              Path, "resolve", side_effect=AssertionError("resolve called before rejection")
                          ):
            with self.assertRaisesRegex(ValueError, "lien symbolique"):
                guard_destination_path(candidate)

    def test_dotdot_cannot_hide_a_preceding_link_component(self):
        linked_parent = self.root / "synthetic-link"
        candidate = linked_parent / ".." / "real" / "output.pdf"
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=self._synthetic_parent_link(linked_parent)), patch.object(
                              Path, "resolve", side_effect=AssertionError("resolve called before rejection")
                          ):
            with self.assertRaisesRegex(ValueError, "lien symbolique"):
                guard_destination_path(candidate)

    def test_dispatcher_refuses_linked_output_for_pdf_and_office_operations(self):
        linked_parent = self.root / "synthetic-link"
        candidate = linked_parent / "output.pdf"
        requests = (
            ("compression", {"profile": "smaller_only"}),
            ("fusion", {}),
            ("extraction", {}),
            ("decoupage", {"chunk": 1}),
            ("reorganisation", {}),
            ("docx", {}),
            ("xlsx", {}),
            ("pptx", {}),
        )
        for operation, kwargs in requests:
            with self.subTest(operation=operation), patch.object(
                Path, "is_symlink", autospec=True,
                side_effect=self._synthetic_parent_link(linked_parent)
            ), patch.object(Path, "resolve", side_effect=AssertionError("dispatcher resolved output")):
                target = linked_parent / "chunks" if operation == "decoupage" else candidate
                with self.assertRaisesRegex(ValueError, "lien symbolique"):
                    openpdf_operations.run_operation(operation, [self.source], target, **kwargs)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_sha256)
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_page_service_refuses_linked_output_for_all_page_entrypoints(self):
        linked_parent = self.root / "synthetic-link"
        requests = (
            lambda: page_service.merge([self.source], linked_parent / "merged.pdf"),
            lambda: page_service.extract(self.source, linked_parent / "extracted.pdf", 1, 1),
            lambda: page_service.reorder(self.source, linked_parent / "reordered.pdf", [1]),
            lambda: page_service.split(self.source, linked_parent / "chunks", 1),
        )
        for action in requests:
            with self.subTest(action=action), patch.object(
                Path, "is_symlink", autospec=True,
                side_effect=self._synthetic_parent_link(linked_parent)
            ), patch.object(Path, "resolve", side_effect=AssertionError("page service resolved output")):
                with self.assertRaisesRegex(ValueError, "lien symbolique"):
                    action()
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_sha256)
        self.assertEqual(list(self.chunks.iterdir()), [])

    def test_recovery_directory_is_checked_before_reservation_or_resolve(self):
        linked_parent = self.root / "synthetic-link"
        with patch.object(Path, "is_symlink", autospec=True,
                          side_effect=self._synthetic_parent_link(linked_parent)), patch.object(
                              Path, "resolve", side_effect=AssertionError("recovery resolved linked folder")
                          ):
            with self.assertRaisesRegex(ValueError, "lien symbolique"):
                openpdf_operations.recover_split(linked_parent)

    def test_real_parent_symlink_is_rejected_without_writing_through_alias(self):
        linked_parent = self.root / "real-parent-link"
        linked_parent.symlink_to(self.real_dir, target_is_directory=True)
        destination = linked_parent / "redirected.pdf"
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            guard_destination_path(destination)
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            openpdf_operations.run_operation("compression", [self.source], destination,
                                             profile="smaller_only")
        self.assertFalse((self.real_dir / "redirected.pdf").exists())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_sha256)

    def test_final_file_symlink_to_missing_target_is_rejected(self):
        target = self.real_dir / "not-created.pdf"
        alias = self.root / "final-link.pdf"
        alias.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            guard_destination_path(alias, allow_existing=True)
        self.assertFalse(target.exists())

    def test_existing_destination_remains_unchanged(self):
        destination = self.root / "existing.pdf"
        original = b"preserve existing destination byte-for-byte"
        destination.write_bytes(original)
        with self.assertRaises(FileExistsError):
            page_service.extract(self.source, destination, 1, 1)
        self.assertEqual(destination.read_bytes(), original)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_sha256)

    def test_directory_target_must_exist_and_must_not_be_linked(self):
        self.assertEqual(guard_destination_path(self.chunks, directory=True), self.chunks)
        linked_directory = self.root / "directory-link"
        linked_directory.symlink_to(self.chunks, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "lien symbolique"):
            guard_destination_path(linked_directory, directory=True)
        with self.assertRaisesRegex(ValueError, "Dossier de destination"):
            guard_destination_path(self.root / "missing", directory=True)

    def test_regular_output_path_is_accepted_without_mutating_source(self):
        destination = self.root / "fresh.pdf"
        checked = guard_destination_path(destination)
        self.assertEqual(checked, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_sha256)

    def test_missing_parent_is_rejected_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Dossier parent destination"):
            guard_destination_path(self.root / "missing" / "output.pdf")


if __name__ == "__main__":
    unittest.main()
