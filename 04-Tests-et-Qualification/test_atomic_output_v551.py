"""V551 Windows-native handle publication tests. Author: Abdelhalim Talbi."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))
import openpdf_atomic_output as atomic
import openpdf_windows_handle_publish_v551 as native


class AtomicOutputV551Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "output"
        self.output.mkdir()
        self.moved = self.root / "output-moved"
        self.redirect = self.root / "redirect"
        self.redirect.mkdir()

    def test_backend_fails_closed_off_windows(self):
        if os.name == "nt":
            self.assertTrue(native.supports_windows_native_publication())
        else:
            with self.assertRaises(OSError):
                native.publish_exclusive_windows(
                    self.root / "does-not-exist.pdf", self.root / "out.pdf"
                )
            self.assertFalse((self.root / "out.pdf").exists())

    def test_atomic_dispatcher_routes_windows_to_native_helper(self):
        source = (ROOT / "03-Sources" / "openpdf_atomic_output.py").read_text(encoding="utf-8")
        self.assertIn("from openpdf_windows_handle_publish_v551 import publish_exclusive_windows", source)
        self.assertIn('if os.name == "nt":', source)
        helper = (ROOT / "03-Sources" / "openpdf_windows_handle_publish_v551.py").read_text(encoding="utf-8")
        self.assertIn("NtCreateFile", helper)
        self.assertIn("NtSetInformationFile", helper)
        self.assertIn("_OBJ_DONT_REPARSE", helper)
        self.assertIn("_FILE_LINK_INFORMATION_CLASS = 11", helper)

    @unittest.skipUnless(os.name == "nt", "Requires native Windows file handles")
    def test_windows_publishes_by_handle_and_preserves_staging_name(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"%PDF-1.4\nV551 handle-relative output")
        result = atomic.publish_exclusive(staged, destination)
        self.assertEqual(result, destination)
        self.assertEqual(destination.read_bytes(), staged.read_bytes())
        self.assertTrue(staged.is_file())

    @unittest.skipUnless(os.name == "nt", "Requires native Windows file handles")
    def test_windows_existing_destination_is_never_replaced(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"new bytes")
        destination.write_bytes(b"original bytes")
        with self.assertRaises(FileExistsError):
            atomic.publish_exclusive(staged, destination)
        self.assertEqual(destination.read_bytes(), b"original bytes")
        self.assertTrue(staged.exists())

    def _make_junction(self, link, target):
        # Use PowerShell Junction creation to avoid cmd.exe /c nested-quote parsing.
        env = os.environ.copy()
        env["OPENPDF_TEST_JUNCTION_LINK"] = str(link)
        env["OPENPDF_TEST_JUNCTION_TARGET"] = str(target)
        script = "New-Item -ItemType Junction -Path $env:OPENPDF_TEST_JUNCTION_LINK -Target $env:OPENPDF_TEST_JUNCTION_TARGET -ErrorAction Stop | Out-Null"
        completed = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, check=False,
        )
        self.assertEqual(
            completed.returncode, 0,
            "PowerShell junction creation failed; no security test is counted as passed: " + completed.stdout,
        )
        self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)

    @unittest.skipUnless(os.name == "nt", "Requires native Windows junction semantics")
    def test_windows_junction_ancestor_is_rejected(self):
        staged_real = self.output / "staged.pdf"
        staged_real.write_bytes(b"source")
        junction = self.root / "junction"
        self._make_junction(junction, self.output)
        with self.assertRaises(OSError):
            atomic.publish_exclusive(junction / "staged.pdf", junction / "published.pdf")
        self.assertFalse((self.output / "published.pdf").exists())

    @unittest.skipUnless(os.name == "nt", "Requires native Windows junction semantics")
    def test_windows_dotdot_does_not_hide_junction(self):
        staged_real = self.output / "staged.pdf"
        staged_real.write_bytes(b"source")
        junction = self.root / "junction"
        self._make_junction(junction, self.output)
        staged = junction / ".." / "output" / "staged.pdf"
        destination = junction / ".." / "output" / "published.pdf"
        with self.assertRaises((OSError, ValueError)):
            atomic.publish_exclusive(staged, destination)
        self.assertFalse((self.output / "published.pdf").exists())

    @unittest.skipUnless(os.name == "nt", "Requires native Windows directory handles")
    def test_windows_parent_swap_is_detected_without_redirect(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"anchored bytes")
        original_open = native._open_relative
        swapped = False

        def swap_parent_before_staging_open(kernel32, ntdll, parent, name, desired_access, share_access, options):
            nonlocal swapped
            # Swap after both directory handles are pinned, but before the staging file handle
            # is opened. Once the file is pinned without delete sharing, Windows correctly
            # prevents this rename; this hook exercises the earlier race window instead.
            if name == "staged.pdf" and not swapped:
                self.output.rename(self.moved)
                self.output.mkdir()
                swapped = True
            return original_open(kernel32, ntdll, parent, name, desired_access, share_access, options)

        with patch.object(native, "_open_relative", side_effect=swap_parent_before_staging_open):
            with self.assertRaisesRegex(RuntimeError, "déplacé ou remplacé"):
                atomic.publish_exclusive(staged, destination)
        self.assertTrue(swapped)
        self.assertEqual((self.moved / "published.pdf").read_bytes(), b"anchored bytes")
        self.assertFalse((self.output / "published.pdf").exists())

    @unittest.skipUnless(os.name == "nt", "Requires Windows handle sharing semantics")
    def test_windows_staging_cannot_be_renamed_while_pinned(self):
        staged = self.output / "staged.pdf"
        destination = self.output / "published.pdf"
        staged.write_bytes(b"anchored bytes")
        original_link = native._create_exclusive_link

        def reject_rename_then_link(ntdll, source_handle, parent_handle, leaf):
            try:
                staged.rename(self.output / "staged-swapped.pdf")
            except OSError:
                pass
            else:
                self.fail("Staging name was renameable while the publication handle was pinned")
            return original_link(ntdll, source_handle, parent_handle, leaf)

        with patch.object(native, "_create_exclusive_link", side_effect=reject_rename_then_link):
            atomic.publish_exclusive(staged, destination)
        self.assertEqual(destination.read_bytes(), b"anchored bytes")
        self.assertTrue(staged.exists())
        self.assertFalse((self.output / "staged-swapped.pdf").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
