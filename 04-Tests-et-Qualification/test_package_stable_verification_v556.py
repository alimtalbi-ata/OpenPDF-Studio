"""V556 archive-verification stability tests (static + functional, no Windows binary claim).
Author: Abdelhalim Talbi.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
import package_cumulative_v434 as package


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inventory_rows(version: str):
    version_bytes = (version + "\n").encode("ascii")
    readme_bytes = b"OpenPDF Studio archive verification fixture.\n"
    rows = [
        {"path": "VERSION.txt", "bytes": len(version_bytes), "sha256": _sha(version_bytes)},
        {"path": "01-Application/README.md", "bytes": len(readme_bytes), "sha256": _sha(readme_bytes)},
    ]
    sums = package.render_sha256_sums(rows).encode("ascii")
    rows.append({"path": package.CHECKSUMS, "bytes": len(sums), "sha256": _sha(sums)})
    inventory = json.dumps(sorted(rows, key=lambda row: row["path"]), indent=2).encode("utf-8")
    members = {
        "VERSION.txt": version_bytes,
        "01-Application/README.md": readme_bytes,
        package.CHECKSUMS: sums,
        package.INVENTORY: inventory,
    }
    return members


def _write_archive(path: Path, version: str) -> bytes:
    members = _inventory_rows(version)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in members.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (0o100644 << 16)
            archive.writestr(info, content)
    return path.read_bytes()


class StableArchiveVerificationV556Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive_path = self.root / "fixture.zip"

    def _verify(self, path):
        # The archive deliberately contains no Windows binaries; this isolates the
        # archive parser, checksums, and binding logic from release qualification.
        with mock.patch.object(package, "evidence", return_value=[]):
            return package.verify(path)

    def test_stable_archive_receipt_binds_exact_opened_bytes(self):
        raw = _write_archive(self.archive_path, "51.4")
        result = self._verify(self.archive_path)
        self.assertEqual(result["archive_sha256"], _sha(raw))
        self.assertEqual(result["archive_bytes"], len(raw))
        self.assertEqual(result["verified_files"], 3)

    def test_detects_in_place_mutation_with_same_file_length_during_verification(self):
        original = _write_archive(self.archive_path, "51.4")
        alternate_path = self.root / "alternate.zip"
        alternate = _write_archive(alternate_path, "51.5")
        self.assertEqual(len(original), len(alternate), "fixture must preserve ZIP offsets and file length")
        real_guard = package.validate_local_record_layout
        original_stat = self.archive_path.stat()

        def mutate_after_structural_preflight(archive, infos):
            result = real_guard(archive, infos)
            # Overwrite in place so the descriptor still refers to the same file object.
            # Restore mtime to make digest comparison a meaningful defence beyond mtime.
            self.archive_path.write_bytes(alternate)
            os.utime(self.archive_path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
            return result

        with mock.patch.object(package, "validate_local_record_layout", side_effect=mutate_after_structural_preflight):
            # The unbuffered reader may detect the mutation by CRC while reading
            # the affected member, before the final digest comparison. Both are
            # valid fail-closed outcomes.
            with self.assertRaises((ValueError, zipfile.BadZipFile)) as caught:
                self._verify(self.archive_path)
            self.assertTrue(
                "ZIP content changed" in str(caught.exception)
                or "ZIP path changed" in str(caught.exception)
                or "CRC" in str(caught.exception),
                str(caught.exception),
            )

    @unittest.skipUnless(os.name == "posix", "Replacing an open path depends on POSIX rename semantics")
    def test_detects_path_replacement_while_original_descriptor_is_open(self):
        _write_archive(self.archive_path, "51.4")
        replacement = self.root / "replacement.zip"
        _write_archive(replacement, "51.5")
        real_guard = package.validate_local_record_layout

        def replace_after_structural_preflight(archive, infos):
            result = real_guard(archive, infos)
            os.replace(replacement, self.archive_path)
            return result

        with mock.patch.object(package, "validate_local_record_layout", side_effect=replace_after_structural_preflight):
            with self.assertRaisesRegex(ValueError, "ZIP path changed during verification"):
                self._verify(self.archive_path)

    def test_file_id_identity_does_not_depend_on_platform_ctime_resolution(self):
        from types import SimpleNamespace
        opened = SimpleNamespace(st_dev=7, st_ino=99, st_size=128,
                                 st_mtime_ns=1000, st_ctime_ns=2000)
        named = SimpleNamespace(st_dev=7, st_ino=99, st_size=128,
                                st_mtime_ns=1000, st_ctime_ns=9000)
        self.assertEqual(package._archive_file_identity(opened),
                         package._archive_file_identity(named))

    def test_rejects_mismatched_path_identity_for_open_descriptor(self):
        _write_archive(self.archive_path, "51.4")
        replacement = self.root / "other-file.bin"
        replacement.write_bytes(b"a distinct file")
        with self.archive_path.open("rb") as stream:
            expected = package._archive_file_identity(os.fstat(stream.fileno()))
            with mock.patch.object(package.os, "lstat", return_value=replacement.lstat()):
                with self.assertRaisesRegex(ValueError, "ZIP path changed during verification"):
                    package._assert_archive_path_binding(self.archive_path, stream, expected)

    def test_rejects_non_regular_input_without_hashing_it(self):
        directory = self.root / "not-a-zip-file"
        directory.mkdir()
        with self.assertRaisesRegex(ValueError, "not a regular file"):
            self._verify(directory)

    def test_implementation_uses_same_stream_for_parse_and_digest(self):
        source = (ROOT / "02-Compilation/package_cumulative_v434.py").read_text(encoding="utf-8")
        self.assertIn('open_flags |= getattr(os, "O_NOFOLLOW", 0)', source)
        self.assertIn('os.fdopen(archive_fd, "rb", buffering=0)', source)
        self.assertIn("zipfile.ZipFile(archive_stream)", source)
        self.assertIn("_digest_open_stream(archive_stream)", source)
        self.assertIn("_assert_archive_path_binding(path, archive_stream, expected_identity)", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
