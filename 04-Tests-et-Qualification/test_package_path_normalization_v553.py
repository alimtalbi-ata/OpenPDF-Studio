"""V553 archive path identity tests; no release or Windows evidence is fabricated.
Author: Abdelhalim Talbi.
"""
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
import package_cumulative_v434 as package


class PackagePathNormalizationV553Tests(unittest.TestCase):
    def test_checksum_inventory_rejects_nfkc_casefold_aliases(self):
        rows = [
            {"path": "03-Sources/A.py", "sha256": "a" * 64},
            {"path": "03-Sources/Ａ.py", "sha256": "b" * 64},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate SHA256SUMS path after normalization"):
            package.render_sha256_sums(rows)

    def test_compatibility_separator_cannot_change_path_structure(self):
        with self.assertRaisesRegex(ValueError, "separators change under Unicode normalization"):
            package.archive_path_key("01-Application/sub／file.txt")

    def test_external_zip_rejects_nfkc_casefold_file_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "collision.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr("01-Application/A.txt", b"first")
                    archive.writestr("01-Application/Ａ.txt", b"second")
            with self.assertRaisesRegex(ValueError, "Duplicate ZIP member after Unicode normalization"):
                package.verify(archive_path)

    def test_external_zip_rejects_nfkc_casefold_directory_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "directory-collision.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("01-Application/Ａ/", b"")
                archive.writestr("01-Application/A/", b"")
            with self.assertRaisesRegex(ValueError, "Duplicate ZIP directory after Unicode normalization"):
                package.verify(archive_path)

    def test_file_cannot_be_parent_after_nfkc_normalization(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "parent-collision.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("01-Application/Ａ", b"parent file")
                archive.writestr("01-Application/A/child.txt", b"child")
            with self.assertRaisesRegex(ValueError, "ZIP file/directory collision"):
                package.verify(archive_path)


if __name__ == "__main__":
    unittest.main()
