"""Release checksum-list integrity tests. No Windows build evidence is fabricated."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
import package_cumulative_v434 as package


class PackageIntegrityManifestV552Tests(unittest.TestCase):
    def _rows(self):
        return [
            {"path": "03-Sources/z_module.py", "bytes": 7, "sha256": "b" * 64},
            {"path": package.INVENTORY, "bytes": 9, "sha256": "d" * 64},
            {"path": "01-Application/README.md", "bytes": 5, "sha256": "a" * 64},
            {"path": package.CHECKSUMS, "bytes": 99, "sha256": "c" * 64},
        ]

    def test_render_is_sorted_and_excludes_only_circular_metadata(self):
        text = package.render_sha256_sums(self._rows())
        self.assertEqual(
            text,
            ("a" * 64) + "  01-Application/README.md\n"
            + ("b" * 64) + "  03-Sources/z_module.py\n",
        )

    def test_validator_accepts_exact_manifest_and_rejects_stale_or_tampered(self):
        rows = self._rows()
        valid = package.render_sha256_sums(rows).encode("ascii")
        package.validate_sha256_sums(valid, rows)
        with self.assertRaisesRegex(ValueError, "does not match"):
            package.validate_sha256_sums(valid + b"# stale\n", rows)
        with self.assertRaisesRegex(ValueError, "does not match"):
            package.validate_sha256_sums(valid.replace(b"README.md", b"REAdME.md"), rows)
        with self.assertRaisesRegex(ValueError, "does not match"):
            package.validate_sha256_sums(b"", rows)

    def test_duplicate_paths_are_rejected(self):
        rows = [
            {"path": "03-Sources/a.py", "sha256": "a" * 64},
            {"path": "03-Sources/A.py", "sha256": "b" * 64},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate SHA256SUMS path after normalization"):
            package.render_sha256_sums(rows)

    def test_invalid_paths_and_hashes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP member"):
            package.render_sha256_sums([
                {"path": "../outside.txt", "sha256": "a" * 64},
            ])
        with self.assertRaisesRegex(ValueError, "Invalid SHA256SUMS inventory entry"):
            package.render_sha256_sums([
                {"path": "03-Sources/a.py", "sha256": "not-a-hash"},
            ])

    @unittest.skipUnless(os.name == "posix", "This test requires reliable POSIX symlink creation")
    def test_linked_source_checksum_is_rejected_before_legacy_renaming(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in package.FOLDERS:
                (root / folder).mkdir(parents=True, exist_ok=True)
            actual = root / "07-Manifestes" / "actual.txt"
            actual.write_text("do not follow links", encoding="utf-8")
            (root / package.CHECKSUMS).symlink_to(actual)
            with self.assertRaisesRegex(ValueError, "Unsafe payload symlink"):
                list(package.payload(root, "51.4"))
    def test_old_repository_checksum_list_is_preserved_as_legacy_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in package.FOLDERS:
                (root / folder).mkdir(parents=True, exist_ok=True)
            old = root / package.CHECKSUMS
            old.write_text("deadbeef  stale-file.txt\n", encoding="utf-8")
            files = list(package.payload(root, "51.4"))
            paths = {name for name, _ in files}
            self.assertNotIn(package.CHECKSUMS, paths)
            self.assertIn("07-Manifestes/SHA256SUMS-LEGACY-NOT-CURRENT.txt", paths)
            self.assertEqual(
                next(path.read_text(encoding="utf-8") for name, path in files
                     if name == "07-Manifestes/SHA256SUMS-LEGACY-NOT-CURRENT.txt"),
                "deadbeef  stale-file.txt\n",
            )


if __name__ == "__main__":
    unittest.main()
