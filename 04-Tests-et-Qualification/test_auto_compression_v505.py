"""V50.5 production PDF auto-compression functional/fail-closed regression tests.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_auto_compression_v505 import AutoCompressionPolicy, auto_compress, main


class AutoCompressionV505(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / 'source.pdf'
        self.dst = self.root / 'result.pdf'
        with fitz.open() as doc:
            page = doc.new_page()
            for i in range(20):
                page.insert_text((40, 50 + i * 20), 'OpenPDF Studio V50.5 compression evidence 123456789')
            doc.save(self.src, deflate=False, garbage=0)
        with self.src.open('ab') as f:
            f.write(b' ' * 4096)

    def test_real_pdf_selected_with_full_rgb_gate(self):
        result = auto_compress(self.src, self.dst)
        self.assertEqual(result['status'], 'published')
        self.assertEqual(result['selected_profile'], 'smaller_only')
        self.assertLess(self.dst.stat().st_size, self.src.stat().st_size)
        self.assertEqual(result['cases'][0]['sha256'], result['output_sha256'])
        with fitz.open(self.dst) as doc:
            self.assertIn('OpenPDF Studio', doc[0].get_text())

    def test_multiple_profiles_choose_smallest(self):
        result = auto_compress(self.src, self.dst,
            AutoCompressionPolicy(profiles=('standard', 'smaller_only')))
        self.assertEqual(result['status'], 'published')
        self.assertEqual(len(result['cases']), 2)
        self.assertEqual(result['output_bytes'],
            min(c['bytes'] for c in result['cases'] if c['status'] == 'accepted'))

    def test_existing_destination_preserved(self):
        self.dst.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):
            auto_compress(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b'KEEP')

    def test_source_equals_destination_refused(self):
        with self.assertRaises((ValueError, FileExistsError)):
            auto_compress(self.src, self.src)

    def test_invalid_profile_and_duplicate_refused(self):
        for profiles in [(), ('bad',), ('standard', 'standard'), ['standard']]:
            with self.subTest(profiles=profiles), self.assertRaises(ValueError):
                AutoCompressionPolicy(profiles=profiles)

    def test_invalid_thresholds_refused(self):
        for args in [{'min_saving_percent': float('nan')},
                     {'max_page_mae': True}, {'max_input_bytes': True},
                     {'max_page_changed_fraction': 2.0}]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                AutoCompressionPolicy(**args)

    def test_source_byte_budget_before_publication(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            auto_compress(self.src, self.dst, AutoCompressionPolicy(max_input_bytes=10))
        self.assertFalse(self.dst.exists())

    def test_symlink_input_rejected(self):
        link = self.root / 'link.pdf'
        try:
            link.symlink_to(self.src)
        except (OSError, NotImplementedError):
            self.skipTest('symlink unsupported')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            auto_compress(link, self.dst)
        self.assertFalse(self.dst.exists())

    def test_quality_gate_rejects_before_publication(self):
        result = auto_compress(self.src, self.dst,
            AutoCompressionPolicy(min_saving_percent=99.99))
        self.assertEqual(result['status'], 'no_compliant_gain')
        self.assertEqual(result['cases'][0]['status'], 'rejected')
        self.assertFalse(self.dst.exists())

    def test_corrupt_pdf_never_published(self):
        self.src.write_bytes(b'%PDF-1.7 invalid content')
        result = auto_compress(self.src, self.dst)
        self.assertEqual(result['status'], 'no_compliant_gain')
        self.assertEqual(result['cases'][0]['status'], 'rejected')
        self.assertFalse(self.dst.exists())

    def test_engine_failure_does_not_publish(self):
        with patch('openpdf_auto_compression_v505.execute_compression',
                   side_effect=RuntimeError('injected')):
            result = auto_compress(self.src, self.dst)
        self.assertEqual(result['status'], 'no_compliant_gain')
        self.assertFalse(self.dst.exists())

    def test_concurrent_destination_creation_never_overwritten(self):
        from openpdf_auto_compression_v505 import publish_exclusive as actual
        def race(temp, dest):
            Path(dest).write_bytes(b'OTHER PROCESS')
            return actual(temp, dest)
        with patch('openpdf_auto_compression_v505.publish_exclusive', side_effect=race):
            with self.assertRaises(FileExistsError):
                auto_compress(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b'OTHER PROCESS')

    def test_source_change_during_execution_fails_closed(self):
        from openpdf_auto_compression_v505 import execute_compression as actual
        def mutate(request):
            receipt = actual(request)
            with self.src.open('ab') as f:
                f.write(b'X')
            return receipt
        with patch('openpdf_auto_compression_v505.execute_compression', side_effect=mutate):
            with self.assertRaisesRegex(RuntimeError, 'modifiée'):
                auto_compress(self.src, self.dst)
        self.assertFalse(self.dst.exists())

    def test_guided_ui_auto_requires_consent_and_preview(self):
        from openpdf_compression_v327 import guided_compress
        class App:
            busy = False
            _v272_busy = False
            _openpdf_skip_diagnostic_dialog = True
            def __init__(self): self.calls = []
            def _run_pdf(self, *args): self.calls.append(args)
        app = App()
        with patch('tkinter.messagebox.askyesno', return_value=True) as consent, \
             patch('openpdf_preview_v326.preview_dialog', return_value=True) as preview:
            self.assertTrue(guided_compress(app, ask_source=lambda: str(self.src),
                ask_destination=lambda _: str(self.dst), choose_profile=lambda: 'auto_quality'))
        self.assertEqual(app.calls[0][0].__name__, 'auto_compress_gui')
        self.assertEqual(app.calls[0][1:], (str(self.src), str(self.dst)))
        consent.assert_called_once()
        preview.assert_called_once()

    def test_guided_ui_auto_refuses_without_consent(self):
        from openpdf_compression_v327 import guided_compress
        class App:
            busy = False
            _v272_busy = False
            _openpdf_skip_diagnostic_dialog = True
            def __init__(self): self.calls = []
            def _run_pdf(self, *args): self.calls.append(args)
        app = App()
        with patch('tkinter.messagebox.askyesno', return_value=False):
            self.assertFalse(guided_compress(app, ask_source=lambda: str(self.src),
                ask_destination=lambda _: str(self.dst), choose_profile=lambda: 'auto_quality'))
        self.assertEqual(app.calls, [])

    def test_cli_real_pdf(self):
        self.assertEqual(main([str(self.src), str(self.dst)]), 0)
        self.assertTrue(self.dst.is_file())


if __name__ == '__main__':
    unittest.main()
