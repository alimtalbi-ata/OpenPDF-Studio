"""V554 ZIP expansion-amplification guard tests.
Author: Abdelhalim Talbi. These are deterministic functional security tests,
not proof of a Windows release build.
"""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
import package_cumulative_v434 as package


class PackageExpansionRatioV554Tests(unittest.TestCase):
    def test_external_zip_rejects_large_single_member_expansion_bomb_before_inventory_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "member-bomb.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                archive.writestr("03-Sources/repeated.bin", b"Z" * (2 * 1024 * 1024))
            with self.assertRaisesRegex(ValueError, "ZIP member expansion ratio exceeded"):
                package.verify(archive_path)

    def test_external_zip_rejects_aggregate_expansion_bomb_of_small_members(self):
        # Each member stays below the per-member 1 MiB threshold. Together the
        # entries exceed 1 MiB and their combined ratio exceeds the archive cap.
        pattern = bytes(range(256)) * 16
        payload = pattern * 120
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "aggregate-bomb.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for index in range(3):
                    archive.writestr(f"03-Sources/chunk-{index}.bin", payload)
            with zipfile.ZipFile(archive_path) as archive:
                infos = [item for item in archive.infolist() if not item.is_dir()]
                self.assertTrue(all(item.file_size < package.RATIO_CHECK_MIN_UNCOMPRESSED for item in infos))
                with self.assertRaisesRegex(ValueError, "ZIP archive expansion ratio exceeded"):
                    package.validate_archive_resources(infos)
            with self.assertRaisesRegex(ValueError, "ZIP archive expansion ratio exceeded"):
                package.verify(archive_path)

    def test_bounded_compression_ratio_is_accepted_by_resource_preflight(self):
        # A repetitive but bounded corpus (~84:1 per this fixture) must remain
        # below the 100:1 archive cap when entries are individually small.
        pattern = bytes(range(256)) * 16
        payload = pattern * 10
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "bounded.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for index in range(30):
                    archive.writestr(f"03-Sources/chunk-{index:02}.bin", payload)
            with zipfile.ZipFile(archive_path) as archive:
                infos = [item for item in archive.infolist() if not item.is_dir()]
                package.validate_archive_resources(infos)

    def test_invalid_central_directory_sizes_are_rejected(self):
        class Entry:
            filename = "03-Sources/invalid.bin"
            compress_size = 1
            file_size = -1

        with self.assertRaisesRegex(ValueError, "Invalid ZIP member sizes"):
            package.validate_archive_resources([Entry()])


if __name__ == "__main__":
    unittest.main()
