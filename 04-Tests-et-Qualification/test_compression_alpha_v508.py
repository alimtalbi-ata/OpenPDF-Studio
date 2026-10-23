"""V50.8: real-PDF alpha fidelity and fail-closed publication tests.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_auto_compression_v505 import auto_compress, AutoCompressionPolicy
from openpdf_compression_alpha_v508 import verify_alpha_fidelity
from openpdf_compression_acceptance_v489 import AcceptancePolicy


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CompressionAlphaV508(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / 'transparent-source.pdf'
        self.dst = self.root / 'result.pdf'
        with fitz.open() as doc:
            first = doc.new_page(width=240, height=200)
            first.draw_rect(fitz.Rect(20, 20, 120, 110), fill=(1, 0, 0),
                            color=None, fill_opacity=0.5)
            first.insert_text((30, 145), 'OpenPDF Studio V50.8 transparency')
            second = doc.new_page(width=260, height=190)
            second.draw_circle((80, 70), 45, fill=(0, 0, 1), color=None,
                               fill_opacity=0.75)
            second.set_rotation(90)
            doc.set_metadata({'title': 'Alpha fidelity V50.8',
                              'author': 'Abdelhalim Talbi'})
            doc.save(self.src, deflate=False, garbage=0)
        with self.src.open('ab') as stream:
            stream.write(b' ' * 6000)

    def _check(self, left=None, right=None, policy=None, **overrides):
        left, right = left or self.src, right or self.dst
        kwargs = dict(source_sha256=digest(left), candidate_sha256=digest(right))
        kwargs.update(overrides)
        return verify_alpha_fidelity(left, right, policy or AcceptancePolicy(), **kwargs)

    def test_real_compression_preserves_transparency_and_rotation(self):
        before = digest(self.src)
        report = auto_compress(self.src, self.dst)
        self.assertEqual(report['status'], 'published', report)
        self.assertEqual(report['alpha_verification'], 'v50.8-exact-alpha-at-bounded-scale')
        alpha = report['selected_quality']['alpha']
        self.assertEqual(alpha['pages_verified'], 2)
        self.assertEqual(alpha['alpha_mismatch_pixels'], 0)
        self.assertGreater(alpha['translucent_pixels'], 0)
        self.assertGreater(alpha['transparent_pixels'], 0)
        self.assertEqual(alpha['pixels_verified'], report['selected_quality']['pixels_compared'])
        self.assertEqual(alpha['candidate_sha256'], report['output_sha256'])
        self.assertEqual(digest(self.src), before)
        with fitz.open(self.dst) as doc:
            self.assertEqual(doc.page_count, 2)
            self.assertEqual(doc[1].rotation, 90)
            self.assertEqual(doc.metadata['title'], 'Alpha fidelity V50.8')

    def test_rgb_white_equivalent_but_alpha_different_is_rejected(self):
        blank, white = self.root / 'blank.pdf', self.root / 'white.pdf'
        with fitz.open() as doc:
            doc.new_page(width=200, height=150)
            doc.save(blank)
        with fitz.open() as doc:
            page = doc.new_page(width=200, height=150)
            page.draw_rect(page.rect, fill=(1, 1, 1), color=None)
            doc.save(white)
        with fitz.open(blank) as a, fitz.open(white) as b:
            self.assertEqual(a[0].get_pixmap(alpha=False).samples,
                             b[0].get_pixmap(alpha=False).samples)
        with self.assertRaisesRegex(RuntimeError, 'Alpha channel differs'):
            self._check(blank, white)

    def test_direct_verified_candidate_has_zero_mismatch(self):
        self.assertEqual(auto_compress(self.src, self.dst)['status'], 'published')
        report = self._check()
        self.assertEqual(report['alpha_mismatch_pixels'], 0)
        self.assertEqual(report['pages_verified'], 2)

    def test_bad_source_digest_rejected(self):
        self.assertEqual(auto_compress(self.src, self.dst)['status'], 'published')
        with self.assertRaisesRegex(RuntimeError, 'hash disagrees'):
            self._check(source_sha256='0' * 64)

    def test_bad_candidate_digest_rejected(self):
        self.assertEqual(auto_compress(self.src, self.dst)['status'], 'published')
        with self.assertRaisesRegex(RuntimeError, 'hash disagrees'):
            self._check(candidate_sha256='0' * 64)

    def test_invalid_hash_format_rejected(self):
        self.assertEqual(auto_compress(self.src, self.dst)['status'], 'published')
        for value in ('z' * 64, '', True, 'A' * 64):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self._check(candidate_sha256=value)

    def test_invalid_policy_rejected(self):
        self.assertEqual(auto_compress(self.src, self.dst)['status'], 'published')
        with self.assertRaises(TypeError):
            self._check(policy=object())

    def test_page_geometry_change_rejected(self):
        with fitz.open() as doc:
            doc.new_page(width=240, height=201)
            doc.new_page(width=260, height=190)
            doc.save(self.dst)
        with self.assertRaisesRegex(RuntimeError, 'geometry differs'):
            self._check()

    def test_encrypted_candidate_rejected(self):
        with fitz.open(self.src) as doc:
            doc.save(self.dst, encryption=fitz.PDF_ENCRYPT_AES_256,
                     owner_pw='owner', user_pw='user')
        with self.assertRaisesRegex(RuntimeError, 'Encrypted'):
            self._check()

    def test_budget_rejected_before_raster(self):
        with fitz.open(self.src) as doc:
            doc.save(self.dst)
        with self.assertRaisesRegex(RuntimeError, 'page pixel budget'):
            self._check(policy=AcceptancePolicy(max_pixels_per_page=10000, render_scale=2.0))

    def test_no_publish_when_alpha_gate_fails(self):
        with patch('openpdf_auto_compression_v505.verify_alpha_fidelity',
                   side_effect=RuntimeError('Injected alpha mismatch')):
            report = auto_compress(self.src, self.dst)
        self.assertEqual(report['status'], 'no_compliant_gain', report)
        self.assertEqual(report['cases'][0]['status'], 'rejected')
        self.assertIn('Injected alpha mismatch', report['cases'][0]['error'])
        self.assertFalse(self.dst.exists())
        self.assertFalse(list(self.root.glob('.openpdf-auto-*')))

    def test_existing_destination_preserved(self):
        self.dst.write_bytes(b'KEEP-EXISTING')
        with self.assertRaises(FileExistsError):
            auto_compress(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b'KEEP-EXISTING')

    def test_symlink_candidate_rejected(self):
        other = self.root / 'other.pdf'
        with fitz.open(self.src) as doc:
            doc.save(other)
        try:
            self.dst.symlink_to(other)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        with self.assertRaisesRegex(RuntimeError, 'regular PDFs'):
            self._check()

    def test_direct_rejects_non_pdf(self):
        self.dst.write_bytes(b'NOT A PDF')
        with self.assertRaisesRegex(RuntimeError, 'Unreadable PDF'):
            self._check()


if __name__ == '__main__':
    unittest.main()
