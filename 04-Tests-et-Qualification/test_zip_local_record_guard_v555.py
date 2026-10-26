"""V555 raw ZIP metadata and local-record integrity regressions.
Author: Abdelhalim Talbi. Synthetic archives are test fixtures, not release evidence.
"""
from __future__ import annotations
import struct
import sys
import tempfile
import unittest
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-Compilation"))
from zip_local_record_guard_v555 import validate_local_record_layout
import package_cumulative_v434 as package

LOCAL = struct.Struct("<4s5H3I2H")
CENTRAL = struct.Struct("<4s6H3I5H2I")
EOCD = struct.Struct("<4s4H2IH")
LOCAL_SIG = b"PK\x03\x04"
CENTRAL_SIG = b"PK\x01\x02"
EOCD_SIG = b"PK\x05\x06"
DD_SIG = b"PK\x07\x08"


def _local(name, payload, *, flags=0, method=zipfile.ZIP_STORED, crc=None,
           compressed_size=None, uncompressed_size=None, extra=b""):
    raw = name.encode("cp437")
    crc = zlib.crc32(payload) & 0xFFFFFFFF if crc is None else crc
    compressed_size = len(payload) if compressed_size is None else compressed_size
    uncompressed_size = len(payload) if uncompressed_size is None else uncompressed_size
    return LOCAL.pack(LOCAL_SIG, 20, flags, method, 0, 0, crc, compressed_size,
                      uncompressed_size, len(raw), len(extra)) + raw + extra


def _central(name, payload, offset, *, flags=0, method=zipfile.ZIP_STORED,
             crc=None, compressed_size=None, uncompressed_size=None, extra=b""):
    raw = name.encode("cp437")
    crc = zlib.crc32(payload) & 0xFFFFFFFF if crc is None else crc
    compressed_size = len(payload) if compressed_size is None else compressed_size
    uncompressed_size = len(payload) if uncompressed_size is None else uncompressed_size
    return CENTRAL.pack(CENTRAL_SIG, 20, 20, flags, method, 0, 0, crc,
                        compressed_size, uncompressed_size, len(raw), len(extra),
                        0, 0, 0, 0, offset) + raw + extra


def _write_manual_zip(path, local_records, central_entries, count):
    central_offset = len(local_records)
    eocd = EOCD.pack(EOCD_SIG, 0, 0, count, count, len(central_entries), central_offset, 0)
    path.write_bytes(local_records + central_entries + eocd)


def _guard(path):
    with zipfile.ZipFile(path, "r") as archive:
        return validate_local_record_layout(archive, archive.infolist())


def _normal_zip(path, name="03-Sources/safe.txt", payload=b"safe payload",
                compression=zipfile.ZIP_STORED, extra=b""):
    item = zipfile.ZipInfo(name)
    item.compress_type = compression
    item.extra = extra
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(item, payload)


def _unicode_path_extra(name, alias, *, crc_override=None):
    raw = name.encode("cp437")
    crc = zlib.crc32(raw) & 0xFFFFFFFF if crc_override is None else crc_override
    data = bytes((1,)) + struct.pack("<I", crc) + alias.encode("utf-8")
    return struct.pack("<HH", 0x7075, len(data)) + data


class ZipLocalRecordGuardV555Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_accepts_normal_stored_and_deflated_archives(self):
        for index, compression in enumerate((zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
            path = self.root / f"normal-{index}.zip"
            _normal_zip(path, payload=b"release-data-" * 50, compression=compression)
            result = _guard(path)
            self.assertEqual(result["entries"], 1)
            self.assertEqual(result["overlapping_records"], 0)

    def test_accepts_zip64_local_size_fields_for_a_small_member(self):
        path = self.root / "zip64-local-sizes.zip"
        with zipfile.ZipFile(path, "w") as archive:
            with archive.open("03-Sources/zip64.txt", "w", force_zip64=True) as stream:
                stream.write(b"small payload with ZIP64 local fields")
        self.assertEqual(_guard(path)["entries"], 1)

    def test_rejects_nul_filename_truncated_by_zipfile(self):
        path = self.root / "nul-name.zip"
        name = "03-Sources/safe.txt"
        _normal_zip(path, name=name)
        data = bytearray(path.read_bytes())
        with zipfile.ZipFile(path) as archive:
            central = archive.start_dir
            index = name.index(".")
        data[30 + index] = 0
        data[central + 46 + index] = 0
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "name contains NUL"):
            _guard(path)
        # Integration contract: the cumulative verifier rejects it before inventory reads.
        with self.assertRaisesRegex(ValueError, "name contains NUL"):
            package.verify(path)

    def test_rejects_local_name_that_differs_from_central_directory(self):
        path = self.root / "local-name-mismatch.zip"
        _normal_zip(path)
        data = bytearray(path.read_bytes())
        data[30] = ord("9")
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "local/central filename mismatch"):
            _guard(path)

    def test_rejects_local_compression_method_mismatch(self):
        path = self.root / "method-mismatch.zip"
        _normal_zip(path, payload=b"small stored data")
        data = bytearray(path.read_bytes())
        struct.pack_into("<H", data, 8, zipfile.ZIP_DEFLATED)
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "compression-method mismatch"):
            _guard(path)

    def test_rejects_local_flag_mismatch(self):
        path = self.root / "flag-mismatch.zip"
        _normal_zip(path)
        data = bytearray(path.read_bytes())
        struct.pack_into("<H", data, 6, 0x0008)
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "flag mismatch"):
            _guard(path)

    def test_rejects_local_crc_and_size_mismatch(self):
        for label, offset, fmt, value, expected in (
            ("crc", 14, "<I", 123, "CRC mismatch"),
            ("size", 18, "<I", 2, "size mismatch"),
        ):
            with self.subTest(field=label):
                path = self.root / f"{label}-mismatch.zip"
                _normal_zip(path, payload=b"four")
                data = bytearray(path.read_bytes())
                struct.pack_into(fmt, data, offset, value)
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, expected):
                    _guard(path)

    def test_rejects_conflicting_info_zip_unicode_path_alias(self):
        path = self.root / "unicode-path-alias.zip"
        name = "03-Sources/safe.txt"
        _normal_zip(path, name=name, extra=_unicode_path_extra(name, "03-Sources/../evil.txt"))
        with self.assertRaisesRegex(ValueError, "rewritten by Unicode extra metadata"):
            _guard(path)

    def test_rejects_unicode_path_crc_mismatch(self):
        path = self.root / "unicode-path-crc.zip"
        name = "03-Sources/safe.txt"
        _normal_zip(path, name=name, extra=_unicode_path_extra(name, name, crc_override=1))
        with self.assertRaisesRegex(ValueError, "Unicode Path CRC mismatch"):
            _guard(path)

    def test_rejects_duplicate_unicode_path_extra_field(self):
        path = self.root / "unicode-path-duplicate.zip"
        name = "03-Sources/safe.txt"
        one = _unicode_path_extra(name, name)
        _normal_zip(path, name=name, extra=one + one)
        with self.assertRaisesRegex(ValueError, "Duplicate ZIP .* security-sensitive extra field"):
            _guard(path)

    def test_rejects_overlapping_local_record_spans(self):
        path = self.root / "overlap.zip"
        a_name, b_name, b_payload = "03-Sources/a.bin", "03-Sources/b.bin", b"B"
        b_local = _local(b_name, b_payload)
        prefix, suffix = b"before", b"after"
        a_payload = prefix + b_local + b_payload + suffix
        a_record = _local(a_name, a_payload) + a_payload
        b_offset = 30 + len(a_name.encode("cp437")) + len(prefix)
        central = _central(a_name, a_payload, 0) + _central(b_name, b_payload, b_offset)
        _write_manual_zip(path, a_record, central, 2)
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(len(archive.infolist()), 2)
            self.assertEqual(archive.infolist()[1].header_offset, b_offset)
        with self.assertRaisesRegex(ValueError, "Overlapping ZIP local records"):
            _guard(path)

    def test_accepts_and_validates_a_well_formed_data_descriptor(self):
        path = self.root / "descriptor-valid.zip"
        name = "03-Sources/descriptor.bin"
        raw, payload = name.encode("cp437"), b"descriptor payload"
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header = LOCAL.pack(LOCAL_SIG, 20, 0x0008, zipfile.ZIP_STORED, 0, 0,
                            0, 0, 0, len(raw), 0) + raw
        descriptor = DD_SIG + struct.pack("<III", crc, len(payload), len(payload))
        local_records = header + payload + descriptor
        central = _central(name, payload, 0, flags=0x0008, crc=crc)
        _write_manual_zip(path, local_records, central, 1)
        self.assertEqual(_guard(path)["entries"], 1)

    def test_accepts_well_formed_zip64_data_descriptor(self):
        path = self.root / "descriptor-zip64-valid.zip"
        name = "03-Sources/descriptor64.bin"
        raw, payload = name.encode("cp437"), b"zip64 descriptor"
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        zip64_data = struct.pack("<QQ", 0, 0)
        extra = struct.pack("<HH", 0x0001, len(zip64_data)) + zip64_data
        header = LOCAL.pack(LOCAL_SIG, 45, 0x0008, zipfile.ZIP_STORED, 0, 0,
                            0, 0xFFFFFFFF, 0xFFFFFFFF, len(raw), len(extra)) + raw + extra
        descriptor = DD_SIG + struct.pack("<IQQ", crc, len(payload), len(payload))
        local_records = header + payload + descriptor
        central = _central(name, payload, 0, flags=0x0008, crc=crc)
        _write_manual_zip(path, local_records, central, 1)
        self.assertEqual(_guard(path)["entries"], 1)

    def test_rejects_corrupt_data_descriptor_before_member_read(self):
        path = self.root / "descriptor-corrupt.zip"
        name = "03-Sources/descriptor.bin"
        raw, payload = name.encode("cp437"), b"descriptor payload"
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header = LOCAL.pack(LOCAL_SIG, 20, 0x0008, zipfile.ZIP_STORED, 0, 0,
                            0, 0, 0, len(raw), 0) + raw
        descriptor = DD_SIG + struct.pack("<III", crc ^ 0x1, len(payload), len(payload))
        local_records = header + payload + descriptor
        central = _central(name, payload, 0, flags=0x0008, crc=crc)
        _write_manual_zip(path, local_records, central, 1)
        with self.assertRaisesRegex(ValueError, "data descriptor does not match"):
            _guard(path)

    def test_rejects_encrypted_or_masked_header_flags(self):
        path = self.root / "encrypted.zip"
        name = "03-Sources/secret.bin"
        raw, payload = name.encode("cp437"), b"x"
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header = LOCAL.pack(LOCAL_SIG, 20, 0x0001, zipfile.ZIP_STORED, 0, 0,
                            crc, 1, 1, len(raw), 0) + raw + payload
        central = _central(name, payload, 0, flags=0x0001)
        _write_manual_zip(path, header, central, 1)
        with self.assertRaisesRegex(ValueError, "Encrypted or masked"):
            _guard(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
