"""Cross-platform regression tests for V50.3 restored runtime modules.
These tests do not constitute a native Windows installer qualification.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import hashlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_atomic_output import publish_exclusive
from openpdf_source_integrity_v430 import fingerprint_source, verify_source_unchanged
from openpdf_page_source_integrity_v435 import snapshot_source, verify_source
from openpdf_split_integrity_v449 import file_sha256, verify_staged
from openpdf_inno_recipe_v491 import render_recipe, ensure_recipe


class RestoredRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_atomic_publication_preserves_existing_file(self):
        source, dest = self.root/'tmp.pdf', self.root/'final.pdf'
        source.write_bytes(b'%PDF-1.4\nnew')
        dest.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            publish_exclusive(source, dest)
        self.assertEqual(dest.read_bytes(), b'original')

    def test_atomic_publication_new_output(self):
        source, dest = self.root/'tmp.pdf', self.root/'final.pdf'
        source.write_bytes(b'%PDF-1.4\nnew')
        self.assertEqual(publish_exclusive(source, dest), dest)
        self.assertEqual(dest.read_bytes(), source.read_bytes())

    def test_atomic_publication_unsupported_volume_fails_closed(self):
        source, dest = self.root/'tmp.pdf', self.root/'final.pdf'
        source.write_bytes(b'nonempty')
        with patch('openpdf_atomic_output.os.link', side_effect=OSError('unsupported')):
            with self.assertRaises(OSError):
                publish_exclusive(source, dest)
        self.assertFalse(dest.exists())

    def test_atomic_publication_empty_file_rejected(self):
        source, dest = self.root/'tmp.pdf', self.root/'final.pdf'
        source.touch()
        with self.assertRaises(ValueError):
            publish_exclusive(source, dest)
        self.assertFalse(dest.exists())

    def test_compression_source_change_rejected(self):
        source = self.root/'source.pdf'
        source.write_bytes(b'A'*2048)
        original = fingerprint_source(source)
        source.write_bytes(b'B'*2048)
        with self.assertRaises(RuntimeError):
            verify_source_unchanged(source, original)

    def test_compression_source_unchanged(self):
        source = self.root/'source.pdf'
        source.write_bytes(b'A'*2048)
        original = fingerprint_source(source)
        self.assertEqual(verify_source_unchanged(source, original), hashlib.sha256(b'A'*2048).hexdigest())

    def test_page_source_change_rejected(self):
        source = self.root/'source.pdf'
        source.write_bytes(b'first')
        snapshot = snapshot_source(source)
        source.write_bytes(b'other')
        with self.assertRaises(RuntimeError):
            verify_source(source, snapshot)

    def test_page_source_unchanged(self):
        source = self.root/'source.pdf'
        source.write_bytes(b'first')
        self.assertTrue(verify_source(source, snapshot_source(source)))

    def test_split_digest_mismatch_rejected(self):
        source = self.root/'part.pdf'
        source.write_bytes(b'one')
        digest = file_sha256(source)
        source.write_bytes(b'two')
        with self.assertRaises(RuntimeError):
            verify_staged(self.root, ['part.pdf'], [digest])

    def test_split_digest_unchanged(self):
        source = self.root/'part.pdf'
        source.write_bytes(b'one')
        verify_staged(self.root, ['part.pdf'], [file_sha256(source)])

    def test_inno_recipe_deterministic(self):
        self.assertEqual(render_recipe('50.3'), render_recipe('50.3'))
        self.assertIn('OutputBaseFilename=OpenPDF-Studio-V50.3-Setup', render_recipe('50.3'))
        self.assertIn(r'Source: "dist\OpenPDF-Studio\*"', render_recipe('50.3'))

    def test_inno_recipe_no_clobber(self):
        (self.root/'03-Sources').mkdir()
        (self.root/'VERSION.txt').write_text('50.3\n')
        target = ensure_recipe(self.root)
        self.assertEqual(target, ensure_recipe(self.root))
        target.write_text('custom', encoding='utf-8')
        with self.assertRaises(ValueError):
            ensure_recipe(self.root)
        self.assertEqual(target.read_text(), 'custom')

    def test_inno_recipe_injection_rejected(self):
        for value in ('50.3\n[Run]', '50.3&calc', '../50.3', '50.3.1', ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                render_recipe(value)


if __name__ == '__main__':
    unittest.main()
