"""Tests for exclusive publishing shared by page, Office and OCR services."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "03-Sources"))
from openpdf_atomic_output import publish_exclusive


class AtomicOutputTests(unittest.TestCase):
    def test_new_output(self):
        with tempfile.TemporaryDirectory() as root:
            temp, dest = Path(root) / "temp.bin", Path(root) / "final.bin"
            temp.write_bytes(b"verified")
            self.assertEqual(publish_exclusive(temp, dest), dest)
            self.assertEqual(dest.read_bytes(), b"verified")

    def test_existing_destination_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            temp, dest = Path(root) / "temp.bin", Path(root) / "final.bin"
            temp.write_bytes(b"new")
            dest.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                publish_exclusive(temp, dest)
            self.assertEqual(dest.read_bytes(), b"original")

    def test_unsupported_volume_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            temp, dest = Path(root) / "temp.bin", Path(root) / "final.bin"
            temp.write_bytes(b"new")
            with patch("openpdf_atomic_output.os.link", side_effect=OSError("unsupported")):
                with self.assertRaises(OSError):
                    publish_exclusive(temp, dest)
            self.assertFalse(dest.exists())

    def test_empty_output_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            temp, dest = Path(root) / "temp.bin", Path(root) / "final.bin"
            temp.touch()
            with self.assertRaises(ValueError):
                publish_exclusive(temp, dest)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
