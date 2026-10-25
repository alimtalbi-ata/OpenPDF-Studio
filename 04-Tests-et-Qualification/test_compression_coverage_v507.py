"""V50.7 real-PDF coverage, forged receipt and fail-closed regression tests.
Author: Abdelhalim Talbi.
"""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_auto_compression_v505 import auto_compress, AutoCompressionPolicy
from openpdf_compression_coverage_v507 import verify_render_coverage
from openpdf_compression_acceptance_v489 import AcceptancePolicy


class CoverageV507(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / 'mixed-two-pages.pdf'
        self.dst = self.root / 'output.pdf'
        with fitz.open() as doc:
            first = doc.new_page(width=360, height=260)
            for index in range(7):
                first.insert_text((30, 40 + 24 * index), 'OpenPDF Studio mixed PDF coverage')
            second = doc.new_page(width=410, height=300)
            second.insert_text((35, 65), 'Rotated second page with Unicode: cafe')
            second.set_rotation(90)
            doc.set_metadata({'title': 'OpenPDF coverage V50.7', 'author': 'Abdelhalim Talbi'})
            doc.save(self.src, deflate=False, garbage=0)
        with self.src.open('ab') as stream:
            stream.write(b' ' * 6000)

    def test_two_page_rotated_pdf_has_exact_coverage(self):
        report = auto_compress(self.src, self.dst)
        self.assertEqual(report['status'], 'published', report)
        self.assertEqual(report['coverage_verification'], 'v50.7-exact-pages-and-pixels')
        quality = report['selected_quality']
        self.assertEqual(quality['pages_compared'], 2)
        self.assertEqual(quality['coverage']['pages_verified'], 2)
        self.assertEqual(quality['coverage']['pixels_verified'], quality['pixels_compared'])
        self.assertGreater(quality['pixels_compared'], 0)
        with fitz.open(self.dst) as doc:
            self.assertEqual(doc.page_count, 2)
            self.assertEqual(doc[1].rotation, 90)
            self.assertEqual(doc.metadata['title'], 'OpenPDF coverage V50.7')

    def _corrupt(self, key, value):
        from openpdf_auto_compression_v505 import execute_compression as real_engine
        def altered(request):
            receipt = real_engine(request)
            self.assertTrue(receipt.published)
            audit = {**receipt.metrics.visual_audit, key: value}
            return replace(receipt, visual_audit=audit,
                metrics=replace(receipt.metrics, visual_audit=audit))
        with patch('openpdf_auto_compression_v505.execute_compression', side_effect=altered):
            report = auto_compress(self.src, self.dst)
        self.assertEqual(report['status'], 'no_compliant_gain', report)
        self.assertEqual(report['cases'][0]['status'], 'rejected')
        self.assertFalse(self.dst.exists())
        self.assertEqual(list(self.root.glob('.openpdf-auto-*')), [])
        return report

    def test_forged_one_page_coverage_rejected(self):
        report = self._corrupt('pages_compared', 1)
        self.assertTrue(
            'every PDF page' in report['cases'][0]['error']
            or 'semantic structure evidence' in report['cases'][0]['error'])

    def test_forged_partial_pixel_coverage_rejected(self):
        report = self._corrupt('pixels_compared', 1)
        self.assertIn('every rendered pixel', report['cases'][0]['error'])

    def test_forged_saved_bytes_rejected(self):
        report = self._corrupt('saved_bytes', 123456)
        self.assertIn('saved-byte', report['cases'][0]['error'])

    def test_bool_pixel_count_rejected(self):
        self._corrupt('pixels_compared', True)

    def test_bool_page_count_rejected(self):
        self._corrupt('pages_compared', True)

    def test_direct_rejects_wrong_page_count(self):
        with fitz.open() as doc:
            doc.new_page()
            doc.save(self.dst)
        with self.assertRaisesRegex(RuntimeError, 'every PDF page'):
            verify_render_coverage(self.src, self.dst,
                {'pages_compared': 2, 'pixels_compared': 1, 'saved_bytes': 1},
                AcceptancePolicy())

    def test_direct_rejects_encrypted_pdf(self):
        with fitz.open(self.src) as doc:
            doc.save(self.dst, encryption=fitz.PDF_ENCRYPT_AES_256,
                     owner_pw='owner', user_pw='user')
        with self.assertRaisesRegex(RuntimeError, 'Encrypted'):
            verify_render_coverage(self.src, self.dst,
                {'pages_compared': 2, 'pixels_compared': 1, 'saved_bytes': 1},
                AcceptancePolicy())

    def test_direct_rejects_invalid_audit_or_policy(self):
        for audit, policy in (([], AcceptancePolicy()), ({}, object())):
            with self.subTest(audit=audit), self.assertRaises(TypeError):
                verify_render_coverage(self.src, self.dst, audit, policy)

    def test_destination_collision_preserves_existing(self):
        self.dst.write_bytes(b'PREEXISTING FILE')
        with self.assertRaises(FileExistsError):
            auto_compress(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b'PREEXISTING FILE')

    def test_bad_pdf_is_never_published(self):
        self.src.write_bytes(b'%PDF-1.7\ninvalid')
        report = auto_compress(self.src, self.dst)
        self.assertEqual(report['status'], 'no_compliant_gain')
        self.assertFalse(self.dst.exists())

    def test_source_is_unchanged(self):
        before = self.src.read_bytes()
        auto_compress(self.src, self.dst)
        self.assertEqual(self.src.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
