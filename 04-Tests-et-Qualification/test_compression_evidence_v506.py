"""V50.6: real-PDF measurement provenance and fail-closed receipt regressions.
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
from openpdf_compression_evidence_v506 import verified_evidence


class EvidenceV506(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.pdf'
        self.destination = self.root / 'output.pdf'
        with fitz.open() as pdf:
            page = pdf.new_page(width=320, height=240)
            for index in range(8):
                page.insert_text((20, 30 + 22 * index), 'Compression evidence V50.6 - text')
            pdf.set_metadata({'title': 'OpenPDF Studio V50.6', 'author': 'Abdelhalim Talbi'})
            pdf.save(self.source, deflate=False, garbage=0)
        with self.source.open('ab') as stream:
            stream.write(b' ' * 4096)

    def test_real_pdf_receipt_has_bound_quality_metrics(self):
        report = auto_compress(self.source, self.destination)
        self.assertEqual(report['status'], 'published')
        self.assertEqual(report['schema'], 'openpdf.auto-compression.v50.6')
        case = report['cases'][0]
        self.assertEqual(case['status'], 'accepted')
        self.assertEqual(case['quality'], report['selected_quality'])
        self.assertGreater(case['quality']['pixels_compared'], 0)
        self.assertEqual(case['quality']['max_page_mae'], 0)
        with fitz.open(self.destination) as doc:
            self.assertEqual(doc.metadata['title'], 'OpenPDF Studio V50.6')
            self.assertEqual(doc.metadata['author'], 'Abdelhalim Talbi')

    def _corrupt(self, transform):
        from openpdf_auto_compression_v505 import execute_compression as engine
        def altered(request):
            receipt = engine(request)
            self.assertTrue(receipt.published)
            return transform(receipt)
        with patch('openpdf_auto_compression_v505.execute_compression', side_effect=altered):
            report = auto_compress(self.source, self.destination)
        self.assertEqual(report['status'], 'no_compliant_gain')
        self.assertEqual(report['cases'][0]['status'], 'rejected')
        self.assertFalse(self.destination.exists())
        return report

    def test_missing_audit_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit=None)))

    def test_candidate_hash_mismatch_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit={
            **r.metrics.visual_audit, 'candidate_sha256': '0' * 64})))

    def test_source_hash_mismatch_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit={
            **r.metrics.visual_audit, 'source_sha256': '0' * 64})))

    def test_missing_measurement_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit={
            **r.metrics.visual_audit, 'pixels_compared': 0})))

    def test_forged_low_mae_with_invalid_fraction_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit={
            **r.metrics.visual_audit, 'max_page_changed_fraction': 0.99})))

    def test_wrong_policy_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit={
            **r.metrics.visual_audit, 'policy': {}})))

    def test_saving_percent_mismatch_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, visual_audit={
            **r.metrics.visual_audit, 'saving_percent': 99.0})))

    def test_receipt_visual_audit_disagreement_is_rejected(self):
        self._corrupt(lambda r: replace(r, visual_audit={}))

    def test_wrong_profile_in_metrics_is_rejected(self):
        self._corrupt(lambda r: replace(r, metrics=replace(r.metrics, profile='images_adaptive')))

    def test_bad_values_are_rejected_by_validator(self):
        from types import SimpleNamespace
        from openpdf_compression_acceptance_v489 import AcceptancePolicy
        policy = AcceptancePolicy()
        baseline = dict(accepted=True, source_sha256='a'*64, candidate_sha256='b'*64,
            source_bytes=100, candidate_bytes=50, policy=policy.__dict__,
            evidence='full_rgb_pixels_at_bounded_scale_not_archival_or_print_certification',
            pages_compared=1, pixels_compared=10, max_page_mae=0,
            max_page_changed_fraction=0, saving_percent=50)
        for key, value in [('max_page_mae', float('nan')), ('pixels_compared', True),
                           ('saving_percent', float('inf')), ('pages_compared', -1)]:
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                audit = {**baseline, key: value}
                metrics = SimpleNamespace(visual_audit=audit, published=True, profile='standard',
                    source_sha256='a'*64, source_bytes=100, output_bytes=50)
                receipt = SimpleNamespace(metrics=metrics, visual_audit=audit,
                    published=True, sha256='b'*64, size=50)
                verified_evidence(receipt, source_sha256='a'*64, source_bytes=100,
                    candidate_sha256='b'*64, candidate_bytes=50, profile='standard', policy=policy)


if __name__ == '__main__':
    unittest.main()
