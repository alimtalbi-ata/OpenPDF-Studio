"""V557 strict-JSON release inventory and evidence regression tests.
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
    readme_bytes = b"OpenPDF Studio strict JSON fixture.\n"
    rows = [
        {"path": "VERSION.txt", "bytes": len(version_bytes), "sha256": _sha(version_bytes)},
        {"path": "01-Application/README.md", "bytes": len(readme_bytes), "sha256": _sha(readme_bytes)},
    ]
    sums = package.render_sha256_sums(rows).encode("ascii")
    rows.append({"path": package.CHECKSUMS, "bytes": len(sums), "sha256": _sha(sums)})
    inventory = json.dumps(sorted(rows, key=lambda row: row["path"]), indent=2).encode("utf-8")
    return {
        "VERSION.txt": version_bytes,
        "01-Application/README.md": readme_bytes,
        package.CHECKSUMS: sums,
        package.INVENTORY: inventory,
    }


def _write_archive(path: Path, version: str, *, duplicate_inventory_key: bool = False) -> bytes:
    members = _inventory_rows(version)
    if duplicate_inventory_key:
        raw = members[package.INVENTORY]
        marker = b'"path": "VERSION.txt",'
        if marker not in raw:
            raise AssertionError("Expected inventory fixture row not found")
        members[package.INVENTORY] = raw.replace(
            marker,
            b'"path": "VERSION.txt",\n    "path": "VERSION.txt",',
            1,
        )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in members.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (0o100644 << 16)
            archive.writestr(info, content)
    return path.read_bytes()


class StrictJSONReleaseIntegrityV557Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive_path = self.root / "fixture.zip"

    def _verify(self, path):
        # This fixture intentionally contains no Windows binary receipts.
        with mock.patch.object(package, "evidence", return_value=[]):
            return package.verify(path)

    def test_valid_utf8_json_and_utf8_bom_are_accepted(self):
        self.assertEqual(package.strict_json_loads(b'{"name":"R\xc3\xa9seau"}', label="fixture"), {"name": "Réseau"})
        self.assertEqual(package.strict_json_loads(b'\xef\xbb\xbf{"ok":true}', label="fixture"), {"ok": True})

    def test_duplicate_keys_are_rejected_at_every_nesting_level(self):
        for payload in (
            '{"path":"first","path":"second"}',
            '{"outer":{"sha256":"first","sha256":"second"}}',
            '[{"name":"first","name":"second"}]',
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "Duplicate JSON object key"):
                    package.strict_json_loads(payload, label="fixture")

    def test_non_finite_constants_are_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(ValueError, "Non-finite JSON number"):
                    package.strict_json_loads('{"value":' + token + '}', label="fixture")

    def test_invalid_utf8_and_truncated_json_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Invalid UTF-8 JSON"):
            package.strict_json_loads(b'{"value":"\xff"}', label="fixture")
        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            package.strict_json_loads('{"value":', label="fixture")

    def test_verifier_rejects_duplicate_keys_in_the_real_zip_inventory(self):
        _write_archive(self.archive_path, "51.4", duplicate_inventory_key=True)
        with self.assertRaisesRegex(ValueError, "Duplicate JSON object key"):
            self._verify(self.archive_path)

    def test_verifier_keeps_accepting_consistent_inventory(self):
        raw = _write_archive(self.archive_path, "51.4")
        result = self._verify(self.archive_path)
        self.assertEqual(result["archive_sha256"], _sha(raw))
        self.assertEqual(result["archive_bytes"], len(raw))
        self.assertEqual(result["verified_files"], 3)

    def test_all_release_json_receipts_use_the_strict_decoder(self):
        source = (ROOT / "02-Compilation/package_cumulative_v434.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("json.loads("), 1, "raw json.loads must be confined to strict_json_loads")
        self.assertIn("manifest = strict_json_loads(read(required[2])", source)
        self.assertIn("smoke = strict_json_loads(read(smoke_name)", source)
        self.assertIn("installation = strict_json_loads(read(required[3])", source)
        self.assertIn("rows = strict_json_loads(archive.read(INVENTORY)", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
