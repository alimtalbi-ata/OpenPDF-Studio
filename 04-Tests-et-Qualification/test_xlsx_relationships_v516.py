"""V51.4 OOXML relationship hardening tests (synthetic fixtures, not GUI proof).
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
sys.path.insert(0, str(ROOT / '04-Tests-et-Qualification'))

from openpyxl import Workbook
from openpdf_xlsx_fidelity_v515 import _xlsx_preflight, audit_xlsx_fidelity
from openpdf_conversion_service_v351 import convert_office
from test_xlsx_tables_v514 import fixture

NS = 'http://schemas.openxmlformats.org/package/2006/relationships'


class XlsxRelationshipsV516Tests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.xlsx = self.directory / 'sample.xlsx'
        wb = Workbook()
        wb.active['A1'] = 'Test'
        wb.save(self.xlsx)
        wb.close()

    def inject(self, xml, member='xl/worksheets/_rels/sheet1.xml.rels'):
        with zipfile.ZipFile(self.xlsx, 'a') as archive:
            archive.writestr(member, xml)

    def relationship(self, target, *, mode='', identifier='rId1'):
        mode_attr = f' TargetMode="{mode}"' if mode else ''
        return (f'<Relationships xmlns="{NS}"><Relationship Id="{identifier}" '
                f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                f'Target="{target}"{mode_attr}/></Relationships>')

    def test_standard_openpyxl_workbook_accepted(self):
        _xlsx_preflight(self.xlsx)

    def test_unreferenced_external_relationship_rejected(self):
        self.inject(self.relationship('https://example.invalid/', mode='External'))
        with self.assertRaisesRegex(ValueError, 'externe'):
            _xlsx_preflight(self.xlsx)

    def test_implicit_external_uri_rejected(self):
        self.inject(self.relationship('https://example.invalid/'))
        with self.assertRaisesRegex(ValueError, 'dangereuse'):
            _xlsx_preflight(self.xlsx)

    def test_missing_internal_part_rejected(self):
        self.inject(self.relationship('missing.xml'))
        with self.assertRaisesRegex(ValueError, 'absent'):
            _xlsx_preflight(self.xlsx)

    def test_traversal_outside_archive_rejected(self):
        self.inject(self.relationship('../../../../secret.xml'))
        with self.assertRaisesRegex(ValueError, 'hors archive'):
            _xlsx_preflight(self.xlsx)

    def test_percent_encoded_traversal_rejected(self):
        self.inject(self.relationship('%2e%2e/%2e%2e/%2e%2e/%2e%2e/secret.xml'))
        with self.assertRaisesRegex(ValueError, 'hors archive'):
            _xlsx_preflight(self.xlsx)

    def test_dtd_entity_rejected(self):
        self.inject(f'<!DOCTYPE Relationships [<!ENTITY x "bad">]><Relationships xmlns="{NS}"/>')
        with self.assertRaisesRegex(ValueError, 'DTD'):
            _xlsx_preflight(self.xlsx)

    def test_malformed_xml_rejected(self):
        self.inject('<Relationships')
        with self.assertRaisesRegex(ValueError, 'XML'):
            _xlsx_preflight(self.xlsx)

    def test_duplicate_relationship_ids_rejected(self):
        rel = (f'<Relationship Id="rId1" Type="x" Target="/xl/styles.xml"/>')
        self.inject(f'<Relationships xmlns="{NS}">{rel}{rel}</Relationships>')
        with self.assertRaisesRegex(ValueError, 'Identifiant'):
            _xlsx_preflight(self.xlsx)

    def test_oversized_relationship_part_rejected(self):
        self.inject(' ' * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'volumineuses'):
            _xlsx_preflight(self.xlsx)

    def test_real_pdf_to_xlsx_audit_and_rollback(self):
        pdf = self.directory / 'source.pdf'
        output = self.directory / 'converted.xlsx'
        fixture(pdf)
        convert_office(pdf, output, table_mode=True)
        self.assertEqual(audit_xlsx_fidelity(pdf, output)['status'], 'PASS')
        blocked = self.directory / 'blocked.xlsx'
        with patch('openpdf_xlsx_fidelity_v515._check_xlsx_relationships',
                   side_effect=ValueError('Relation XLSX externe interdite')):
            with self.assertRaisesRegex(ValueError, 'externe'):
                convert_office(pdf, blocked, table_mode=True)
        self.assertFalse(blocked.exists())


if __name__ == '__main__':
    unittest.main()
