"""V51.0 functional tests on synthetic PDF files, not Windows GUI proof.
Author: Abdelhalim Talbi.
"""
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_office_scan_gate_v510 import (
    _union_area, assess_office_source, require_editable_source,
    ScannedPDFRequiresOCRError,
)
from openpdf_conversion_service_v351 import convert_office


class OfficeScanGateV510(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = self.root / 'synthetic.pdf'
        img = Image.new('RGB', (800, 1100), 'white')
        from PIL import ImageDraw
        ImageDraw.Draw(img).text((100, 200), 'RASTER ONLY SCANNED CONTENT', fill='black')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        self.raster = buf.getvalue()

    def pdf(self, *, scan=False, text=False, blank=False, logo=False, mixed=False):
        with fitz.open() as doc:
            page = doc.new_page(width=600, height=800)
            if scan:
                page.insert_image(page.rect, stream=self.raster)
            if logo:
                page.insert_image(fitz.Rect(20, 20, 80, 80), stream=self.raster)
            if text:
                page.insert_text((100, 100), 'EDITABLE PDF TEXT', fontsize=16)
            if mixed:
                doc.new_page().insert_image(fitz.Rect(0, 0, 595, 840), stream=self.raster)
            doc.save(self.source)
        return self.source

    def test_exact_union_avoids_double_count(self):
        self.assertEqual(_union_area([(0, 0, 5, 5), (0, 0, 5, 5)]), 25)
        self.assertEqual(_union_area([(0, 0, 5, 5), (5, 0, 10, 5)]), 50)
        self.assertEqual(_union_area([]), 0)

    def test_scanned_page_detected(self):
        report = assess_office_source(self.pdf(scan=True))
        self.assertEqual(report.scanned_pages, (1,))
        self.assertGreater(report.pages[0]['raster_coverage'], 0.95)
        with self.assertRaises(ScannedPDFRequiresOCRError):
            require_editable_source(report)

    def test_scanned_page_rejected_all_formats_without_temp_files(self):
        self.pdf(scan=True)
        source_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        for fmt in ('docx', 'xlsx', 'pptx'):
            dest = self.root / ('scan.' + fmt)
            with self.assertRaisesRegex(ScannedPDFRequiresOCRError, 'OCR required'):
                convert_office(self.source, dest)
            self.assertFalse(dest.exists())
        self.assertFalse(list(self.root.glob('.openpdf-office-*')))
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), source_hash)

    def test_mixed_text_and_scanned_page_rejected(self):
        self.pdf(text=True, mixed=True)
        report = assess_office_source(self.source)
        self.assertEqual(report.scanned_pages, (2,))
        self.assertTrue(report.pages[0]['has_extractable_text'])
        with self.assertRaisesRegex(ScannedPDFRequiresOCRError, '2'):
            convert_office(self.source, self.root / 'mixed.docx')

    def test_text_layer_on_image_allows_conversion(self):
        self.pdf(scan=True, text=True)
        report = assess_office_source(self.source)
        self.assertEqual(report.scanned_pages, ())
        for fmt in ('docx', 'xlsx', 'pptx'):
            dest = self.root / ('text.' + fmt)
            result = convert_office(self.source, dest)
            self.assertTrue(dest.exists())
            self.assertEqual(result.sha256, hashlib.sha256(dest.read_bytes()).hexdigest())

    def test_blank_page_remains_supported(self):
        self.pdf(blank=True)
        report = assess_office_source(self.source)
        self.assertEqual(report.blank_pages, (1,))
        dest = self.root / 'blank.docx'
        convert_office(self.source, dest)
        self.assertTrue(dest.is_file())

    def test_small_logo_without_text_warns_but_not_scan(self):
        self.pdf(logo=True)
        report = assess_office_source(self.source)
        self.assertEqual(report.non_text_graphics_pages, (1,))
        self.assertEqual(report.scanned_pages, ())
        result = convert_office(self.source, self.root / 'logo.docx')
        self.assertTrue(any('graphiques' in warning for warning in result.warnings))

    def test_existing_destination_preserved(self):
        self.pdf(scan=True)
        dest = self.root / 'protected.docx'
        dest.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):
            convert_office(self.source, dest)
        self.assertEqual(dest.read_bytes(), b'KEEP')

    def test_encrypted_source_rejected(self):
        with fitz.open() as doc:
            doc.new_page().insert_text((70, 100), 'secret')
            doc.save(self.source, encryption=fitz.PDF_ENCRYPT_AES_256,
                     owner_pw='owner', user_pw='user')
        with self.assertRaisesRegex(ValueError, 'Encrypted'):
            assess_office_source(self.source)

    def test_symlink_source_rejected(self):
        self.pdf(text=True)
        link = self.root / 'alias.pdf'
        try:
            link.symlink_to(self.source)
        except OSError:
            self.skipTest('Symlinks not supported')
        with self.assertRaisesRegex(ValueError, 'Invalid PDF'):
            assess_office_source(link)

    def test_threshold_invalid(self):
        self.pdf(text=True)
        for threshold in (0, -1, 1.1):
            with self.assertRaises(ValueError):
                assess_office_source(self.source, raster_threshold=threshold)

    def test_json_cli_exit_status_without_text_leak(self):
        self.pdf(scan=True)
        p = subprocess.run([sys.executable, str(ROOT/'03-Sources'/'openpdf_office_scan_gate_v510.py'),
                            str(self.source)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertTrue(p.stdout.strip(), f'CLI produced no JSON: stderr={p.stderr!r}')
        try:
            result = json.loads(p.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f'Invalid CLI JSON: stdout={p.stdout[:600]!r} stderr={p.stderr[:600]!r}: {exc}')
        self.assertEqual(result['editable_text_gate'], 'blocked_ocr_required')
        self.assertNotIn('RASTER ONLY SCANNED CONTENT', p.stdout)
        self.assertEqual(result['scanned_pages'], [1])


if __name__ == '__main__':
    unittest.main()
