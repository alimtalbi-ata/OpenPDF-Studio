"""V550 tests for directory-handle-anchored publication. Author: Abdelhalim Talbi."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import openpdf_atomic_output as atomic


class AtomicOutputV550Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        self.output.mkdir()
        self.redirect = self.root / "redirect"
        self.redirect.mkdir()

    def test_regular_file_is_published_and_temp_is_preserved(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"%PDF-1.4\nV550 anchored publication")
        self.assertEqual(atomic.publish_exclusive(staged, destination), destination)
        self.assertEqual(destination.read_bytes(), staged.read_bytes())
        self.assertTrue(staged.exists())

    def test_existing_destination_is_never_replaced(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"new bytes")
        destination.write_bytes(b"original bytes")
        with self.assertRaises(FileExistsError):
            atomic.publish_exclusive(staged, destination)
        self.assertEqual(destination.read_bytes(), b"original bytes")
        self.assertEqual(staged.read_bytes(), b"new bytes")

    def test_empty_staging_file_is_rejected(self):
        staged = self.output / "empty.pdf"
        destination = self.output / "published.pdf"
        staged.touch()
        with self.assertRaises(ValueError):
            atomic.publish_exclusive(staged, destination)
        self.assertFalse(destination.exists())

    def test_hardlink_error_fails_closed(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"nonempty")
        with patch.object(atomic, "_supports_anchored_publication", return_value=True), patch.object(atomic.os, "link", side_effect=OSError("simulated unsupported volume")):
            with self.assertRaises(OSError):
                atomic.publish_exclusive(staged, destination)
        self.assertFalse(destination.exists())

    def test_different_parent_directory_is_refused(self):
        staged = self.output / "staged.pdf"
        destination = self.redirect / "published.pdf"
        staged.write_bytes(b"nonempty")
        with self.assertRaisesRegex(ValueError, "same folder|même dossier"):
            atomic.publish_exclusive(staged, destination)
        self.assertFalse(destination.exists())

    def test_final_symlink_staging_entry_is_rejected(self):
        if os.name != "posix":
            self.skipTest("The test runner has no POSIX no-follow openat capability")
        real = self.output / "real.pdf"
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        real.write_bytes(b"real")
        staged.symlink_to(real)
        with self.assertRaises(OSError):
            atomic.publish_exclusive(staged, destination)
        self.assertFalse(destination.exists())

    def test_link_in_parent_chain_is_rejected_before_publication(self):
        if os.name != "posix":
            self.skipTest("Handle-relative no-follow traversal is POSIX-only in V550")
        alias = self.root / "alias"
        alias.symlink_to(self.output, target_is_directory=True)
        staged = alias / "staged.pdf"
        destination = alias / "published.pdf"
        (self.output / "staged.pdf").write_bytes(b"staged")
        with self.assertRaises(OSError):
            atomic.publish_exclusive(staged, destination)
        self.assertFalse((self.output / "published.pdf").exists())

    def test_dotdot_does_not_hide_a_symlink_component(self):
        if os.name != "posix":
            self.skipTest("Handle-relative no-follow traversal is POSIX-only in V550")
        alias = self.root / "alias"
        alias.symlink_to(self.output, target_is_directory=True)
        staged = alias / ".." / "output" / "staged.pdf"
        destination = alias / ".." / "output" / "published.pdf"
        (self.output / "staged.pdf").write_bytes(b"staged")
        with self.assertRaises(OSError):
            atomic.publish_exclusive(staged, destination)
        self.assertFalse((self.output / "published.pdf").exists())

    def test_parent_replacement_during_link_does_not_redirect_write(self):
        if not atomic._supports_anchored_publication():
            self.skipTest("Directory-handle anchoring is not supported on this runner")
        original_dir = self.root / "anchored"
        original_dir.mkdir()
        moved_dir = self.root / "anchored-moved"
        alias_dir = self.root / "attacker-target"
        alias_dir.mkdir()
        staged = original_dir / "staged.pdf"
        destination = original_dir / "published.pdf"
        staged.write_bytes(b"correct inode")
        real_link = os.link
        swapped = False

        def swap_parent_and_link(src, dst, **kwargs):
            nonlocal swapped
            if not swapped:
                original_dir.rename(moved_dir)
                original_dir.symlink_to(alias_dir, target_is_directory=True)
                swapped = True
            return real_link(src, dst, **kwargs)

        with patch.object(atomic, "_supports_anchored_publication", return_value=True), patch.object(atomic.os, "link", side_effect=swap_parent_and_link):
            with self.assertRaisesRegex(RuntimeError, "déplacé ou remplacé"):
                atomic.publish_exclusive(staged, destination)
        self.assertTrue((moved_dir / "published.pdf").is_file())
        self.assertEqual((moved_dir / "published.pdf").read_bytes(), b"correct inode")
        self.assertFalse((alias_dir / "published.pdf").exists())


    def test_temporary_entry_swap_cannot_change_inode_published_on_linux(self):
        if not getattr(atomic, "_HAS_PROC_FD_LINK", False):
            self.skipTest("Linux /proc/self/fd hard-link publication is not available")
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        redirected = self.redirect / "attacker.pdf"
        staged.write_bytes(b"expected opened inode")
        redirected.write_bytes(b"attacker-controlled bytes")
        real_link = os.link
        swapped = False

        def replace_staging_name_and_link(src, dst, **kwargs):
            nonlocal swapped
            if not swapped:
                staged.rename(self.output / "staged-original.pdf")
                staged.symlink_to(redirected)
                swapped = True
            return real_link(src, dst, **kwargs)

        with patch.object(atomic.os, "link", side_effect=replace_staging_name_and_link):
            atomic.publish_exclusive(staged, destination)
        self.assertEqual(destination.read_bytes(), b"expected opened inode")
        self.assertEqual(redirected.read_bytes(), b"attacker-controlled bytes")
        self.assertTrue(staged.is_symlink())
        self.assertEqual((self.output / "staged-original.pdf").read_bytes(), b"expected opened inode")

    def test_path_based_windows_fallback_does_not_claim_full_toctou_support(self):
        source = Path(atomic.__file__).read_text(encoding="utf-8")
        self.assertIn("does not claim complete", source)
        self.assertIn('os.name == "posix"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
