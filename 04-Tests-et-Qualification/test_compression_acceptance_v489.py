"""Real-PDF regression tests for V48.9 read-only compression acceptance.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / '03-Sources' / 'openpdf_compression_acceptance_v489.py'
sys.path.insert(0, str(MODULE.parent))
from openpdf_compression_acceptance_v489 import (
    AcceptancePolicy, CompressionRejected, audit_compression_candidate)


class CompressionAcceptanceV489(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.src = self.root / 'original.pdf'
        self.dst = self.root / 'candidate.pdf'
        with fitz.open() as doc:
            page = doc.new_page(width=320, height=240)
            page.insert_text((40, 50), 'OpenPDF compression test')
            page.draw_rect(fitz.Rect(40, 70, 160, 130), color=(0, 0, 0), fill=(1, 0, 0))
            doc.save(self.src)
        self.dst.write_bytes(self.src.read_bytes())

    def test_real_image_stream_deflate_gain(self):
        # Real PDF compression, not a mocked or estimated byte reduction.
        w, h = 240, 180
        rgb = b''.join(bytes((x // 20 * 10, y // 20 * 10, 60))
                       for y in range(h) for x in range(w))
        with fitz.open() as doc:
            page = doc.new_page(width=320, height=240)
            page.insert_text((20, 20), 'Lossless image stream compression')
            page.insert_image(fitz.Rect(30, 40, 270, 220),
                              pixmap=fitz.Pixmap(fitz.csRGB, w, h, rgb, False))
            doc.save(self.src, deflate=False)
        with fitz.open(self.src) as doc:
            doc.save(self.dst, deflate=True, deflate_images=True, garbage=4)
        receipt = audit_compression_candidate(
            self.src, self.dst, AcceptancePolicy(min_saving_percent=50))
        self.assertGreater(receipt['saving_percent'], 50)
        self.assertEqual(receipt['max_page_mae'], 0)

    def test_exact_copy(self):
        r = audit_compression_candidate(self.src, self.dst)
        self.assertTrue(r['accepted'])
        self.assertEqual(r['max_page_mae'], 0)
        self.assertEqual(r['saving_percent'], 0)
        self.assertGreater(r['pixels_compared'], 0)

    def test_hashes_and_size_evidence(self):
        r = audit_compression_candidate(self.src, self.dst)
        self.assertEqual(len(r['source_sha256']), 64)
        self.assertEqual(r['source_sha256'], r['candidate_sha256'])
        self.assertEqual(r['saved_bytes'], 0)

    def test_size_growth_rejected(self):
        with self.dst.open('ab') as out:
            out.write(b'\n' + b' ' * 200)
        with self.assertRaisesRegex(CompressionRejected, 'gain'):
            audit_compression_candidate(self.src, self.dst)

    def test_required_saving_rejected(self):
        with self.assertRaisesRegex(CompressionRejected, 'gain'):
            audit_compression_candidate(self.src, self.dst, AcceptancePolicy(min_saving_percent=1))

    def test_text_change_rejected(self):
        with fitz.open(self.src) as doc:
            doc[0].insert_text((40, 170), 'changed')
            doc.save(self.dst, incremental=False)
        with self.assertRaisesRegex(CompressionRejected, 'text differs'):
            audit_compression_candidate(self.src, self.dst)

    def test_visual_change_rejected(self):
        with fitz.open(self.src) as doc:
            doc[0].draw_rect(fitz.Rect(0, 0, 320, 240), color=None, fill=(0, 0, 1), overlay=True)
            doc.save(self.dst)
        with self.assertRaisesRegex(CompressionRejected, 'visual quality'):
            audit_compression_candidate(self.src, self.dst)

    def test_page_count_rejected(self):
        with fitz.open(self.src) as doc:
            doc.new_page()
            doc.save(self.dst)
        with self.assertRaisesRegex(CompressionRejected, 'Page count'):
            audit_compression_candidate(self.src, self.dst)

    def test_geometry_rejected(self):
        with fitz.open(self.src) as doc:
            doc[0].set_rotation(90)
            doc.save(self.dst)
        with self.assertRaisesRegex(CompressionRejected, 'geometry'):
            audit_compression_candidate(self.src, self.dst)

    def test_render_budget_rejected_before_render(self):
        with self.assertRaisesRegex(CompressionRejected, 'budget'):
            audit_compression_candidate(self.src, self.dst,
                                        AcceptancePolicy(max_pixels_per_page=10000, render_scale=2))

    def test_same_file_rejected(self):
        with self.assertRaises(CompressionRejected):
            audit_compression_candidate(self.src, self.src)

    def test_invalid_policy(self):
        for opts in ({'render_scale': float('nan')}, {'max_page_mae': True},
                     {'max_pages': 0}, {'pixel_delta': 1.5},
                     {'max_page_changed_fraction': 1.01}):
            with self.subTest(opts=opts), self.assertRaises(ValueError):
                AcceptancePolicy(**opts)

    def test_no_source_mutation(self):
        before = self.src.read_bytes()
        audit_compression_candidate(self.src, self.dst)
        self.assertEqual(self.src.read_bytes(), before)

    def test_cli_json_pass(self):
        result = subprocess.run([sys.executable, str(MODULE), str(self.src), str(self.dst)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"accepted": true', result.stdout)

    def test_cli_json_reject(self):
        result = subprocess.run([sys.executable, str(MODULE), str(self.src), str(self.dst),
                                 '--min-saving-percent', '1'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('"accepted": false', result.stdout)


if __name__ == '__main__':
    unittest.main()
