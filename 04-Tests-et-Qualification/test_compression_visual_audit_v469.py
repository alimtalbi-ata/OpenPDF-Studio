"""V46.9 bounded quantitative compression tests. Author: Abdelhalim Talbi."""
from pathlib import Path
import sys
import tempfile
import unittest
import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_compression_visual_audit_v469 import audit_compression_pair

class CompressionVisualAuditV469(unittest.TestCase):
    def _pdf(self, folder, name, text):
        path = Path(folder) / name
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_text((50, 90), text)
            doc.save(path)
        return path

    def test_identical_render_zero_error(self):
        with tempfile.TemporaryDirectory() as folder:
            a = self._pdf(folder, 'a.pdf', 'OpenPDF visual audit')
            b = Path(folder) / 'b.pdf'
            b.write_bytes(a.read_bytes())
            audit = audit_compression_pair(a, b)
            self.assertEqual((audit.max_page_mae, audit.max_page_changed_fraction), (0, 0))
            self.assertTrue(audit.text_identical)
            self.assertGreater(audit.pixels_sampled, 100)

    def test_difference_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            a = self._pdf(folder, 'a.pdf', 'OpenPDF source')
            b = self._pdf(folder, 'b.pdf', 'Changed output')
            audit = audit_compression_pair(a, b, sample_step=1)
            self.assertFalse(audit.text_identical)
            self.assertGreater(audit.max_page_mae, 0)

    def test_budget_rejects_before_render(self):
        with tempfile.TemporaryDirectory() as folder:
            a = self._pdf(folder, 'a.pdf', 'OpenPDF')
            b = self._pdf(folder, 'b.pdf', 'OpenPDF')
            with self.assertRaisesRegex(ValueError, 'Budget de pixels total'):
                audit_compression_pair(a, b, max_total_pixels=10000)

    def test_bad_parameters_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            a = self._pdf(folder, 'a.pdf', 'OpenPDF')
            b = self._pdf(folder, 'b.pdf', 'OpenPDF')
            for kw in ({'scale': float('nan')}, {'sample_step': True}, {'max_pages': 0}):
                with self.subTest(kw=kw), self.assertRaises(ValueError):
                    audit_compression_pair(a, b, **kw)

    def test_same_source_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            a = self._pdf(folder, 'a.pdf', 'OpenPDF')
            with self.assertRaises(ValueError):
                audit_compression_pair(a, a)

if __name__ == '__main__':
    unittest.main()
