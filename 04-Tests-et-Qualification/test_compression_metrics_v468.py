"""V46.8 compression metrics tests. Author: Abdelhalim Talbi."""
from pathlib import Path
import sys
import tempfile
import unittest
import fitz
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_compression_metrics_v468 import build_metrics
from openpdf_compression_service_v344 import CompressionRequest, execute_compression


class CompressionMetricsV468(unittest.TestCase):
    def _pdf(self, directory):
        source = Path(directory) / 'source.pdf'
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_text((60, 80), 'OpenPDF Studio compression metrics 468')
            doc.save(source)
        return source

    def test_size_and_saving(self):
        m = build_metrics(profile='smaller_only', source_bytes=1000,
                          output_bytes=600, source_sha256='a' * 64,
                          published=True, canonical_engine=True)
        self.assertEqual((m.saved_bytes, m.saving_percent), (400, 40.0))
        self.assertEqual(m.quality_evidence, 'lossless_image_and_render_checks')

    def test_negative_saving_not_hidden(self):
        m = build_metrics(profile='standard', source_bytes=100,
                          output_bytes=125, source_sha256='a' * 64,
                          published=True, canonical_engine=True)
        self.assertEqual(m.saving_percent, -25.0)

    def test_lossy_evidence_is_honest(self):
        for profile in ('images_balanced', 'images_adaptive'):
            m = build_metrics(profile=profile, source_bytes=100,
                              output_bytes=80, source_sha256='a' * 64,
                              published=True, canonical_engine=True)
            self.assertEqual(m.quality_evidence, 'sampled_lossy_render_checks')

    def test_no_gain(self):
        m = build_metrics(profile='smaller_only', source_bytes=100,
                          output_bytes=0, source_sha256='a' * 64,
                          published=False, canonical_engine=True)
        self.assertEqual((m.saved_bytes, m.saving_percent), (0, 0))
        self.assertEqual(m.quality_evidence, 'not_applicable_no_output')

    def test_invalid_receipt_rejected(self):
        with self.assertRaises(ValueError):
            build_metrics(profile='standard', source_bytes=100,
                          output_bytes=0, source_sha256='a' * 64,
                          published=True, canonical_engine=True)

    def test_real_pdf_compression(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._pdf(folder)
            target = Path(folder) / 'compressed.pdf'
            receipt = execute_compression(CompressionRequest(str(source), str(target), 'standard'))
            self.assertTrue(receipt.published)
            self.assertEqual(receipt.metrics.source_bytes, source.stat().st_size)
            self.assertEqual(receipt.metrics.output_bytes, target.stat().st_size)
            with fitz.open(target) as doc:
                self.assertIn('compression metrics 468', doc[0].get_text())

    def test_injected_engine_never_claims_quality(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._pdf(folder)
            target = Path(folder) / 'out.pdf'
            def engine(src, dst, profile):
                Path(dst).write_bytes(Path(src).read_bytes())
                return 'OK'
            receipt = execute_compression(CompressionRequest(str(source), str(target)), engine)
            self.assertEqual(receipt.metrics.quality_evidence, 'unverified_injected_engine')

    def test_mutated_source_rejected_even_when_no_gain(self):
        with tempfile.TemporaryDirectory() as folder:
            source = self._pdf(folder)
            target = Path(folder) / 'out.pdf'
            def engine(src, dst, profile):
                with open(src, 'ab') as stream:
                    stream.write(b'changed')
                return 'Aucun gain : Aucun fichier de sortie modifié'
            with self.assertRaisesRegex(RuntimeError, 'Source modifiée'):
                execute_compression(CompressionRequest(str(source), str(target)), engine)
            self.assertFalse(target.exists())
