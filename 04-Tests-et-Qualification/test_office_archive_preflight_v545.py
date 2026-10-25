"""V545 Office ZIP integrity and cross-platform member-name security tests.
All fixtures are generated locally; no customer documents or claims of human fidelity.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from pathlib import Path
import struct
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))
sys.path.insert(0, str(ROOT / "04-Tests-et-Qualification"))

from openpdf_office_reference_v542 import evaluate_office_reference_corpus
from test_office_reference_v542 import OfficeReferenceV542Tests


class OfficeArchivePreflightV545Tests(unittest.TestCase):
    def setUp(self):
        fixture = OfficeReferenceV542Tests()
        fixture.setUp()
        self.fixture = fixture
        self.addCleanup(fixture.doCleanups)
        self.office, _ = fixture.case("docx", "Archive integrity baseline 2026")
        fixture.case("xlsx", "Second editable office baseline")
        self.manifest = fixture.manifest()

    def append_member(self, name: str, payload: bytes = b"harmless fixture"):
        with zipfile.ZipFile(self.office, "a", compression=zipfile.ZIP_STORED) as package:
            package.writestr(name, payload)

    def test_valid_docx_and_xlsx_still_pass_full_archive_scan(self):
        report = evaluate_office_reference_corpus(self.manifest)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["cases"], 2)

    def test_casefolded_duplicate_member_is_rejected(self):
        self.append_member("WORD/DOCUMENT.XML", b"<ambiguous/>")
        with self.assertRaisesRegex(ValueError, "Ambiguous case-insensitive Office member"):
            evaluate_office_reference_corpus(self.manifest)

    def test_windows_trailing_dot_member_is_rejected(self):
        self.append_member("custom/payload.txt.", b"ambiguous on Windows")
        with self.assertRaisesRegex(ValueError, "Ambiguous or unsafe Windows Office member"):
            evaluate_office_reference_corpus(self.manifest)

    def test_windows_reserved_device_member_is_rejected(self):
        self.append_member("custom/CON.xml", b"reserved device name")
        with self.assertRaisesRegex(ValueError, "Reserved Windows Office member name"):
            evaluate_office_reference_corpus(self.manifest)

    def test_crc_corruption_in_unused_member_is_rejected_before_conversion(self):
        # This member is intentionally not referenced by DOCX relationships. A
        # consumer might never open it, but the archive-wide CRC pass must.
        self.append_member("custom/unused.txt", b"payload whose CRC must be checked")
        with zipfile.ZipFile(self.office, "r") as package:
            info = package.getinfo("custom/unused.txt")
            self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
            offset = info.header_offset
        raw = bytearray(self.office.read_bytes())
        name_length, extra_length = struct.unpack_from("<HH", raw, offset + 26)
        data_offset = offset + 30 + name_length + extra_length
        raw[data_offset] ^= 0x01
        self.office.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "Office archive integrity check failed"):
            evaluate_office_reference_corpus(self.manifest)


if __name__ == "__main__":
    unittest.main()
