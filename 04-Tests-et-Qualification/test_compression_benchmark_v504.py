"""V50.4: real PDF compression benchmark tests, including failure paths.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_compression_benchmark_v504 import BenchmarkPolicy, benchmark_corpus, main


class CompressionBenchmarkV504(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'original.pdf'
        with fitz.open() as doc:
            page = doc.new_page(width=595, height=842)
            for row in range(30):
                page.insert_text((50, 60 + row * 18),
                                 'OpenPDF Studio — measured PDF compression quality 0123456789')
            page.draw_rect(fitz.Rect(50, 680, 450, 760), fill=(0.1, 0.5, 0.8))
            doc.save(self.source, deflate=False, garbage=0)
        # Valid PDF trailing padding: creates a measurable compression opportunity.
        with self.source.open('ab') as stream:
            stream.write(b' ' * 4096)

    def test_real_pdf_size_quality_and_json_receipt(self):
        output = self.root / 'benchmark'
        report = benchmark_corpus([self.source], output,
                                  BenchmarkPolicy(profiles=('standard', 'smaller_only')))
        self.assertEqual(len(report['cases']), 2)
        self.assertEqual(report['counts']['rejected'], 0)
        self.assertEqual(report['counts']['published'], 2)
        self.assertEqual(report['schema'], 'openpdf.compression.benchmark.v50.4')
        self.assertEqual(report['cases'][0]['quality']['pixel_step'], 1)
        self.assertTrue(report['cases'][0]['quality']['text_identical'])
        self.assertTrue(report['cases'][0]['quality']['geometry_identical'])
        self.assertEqual(report['cases'][0]['quality']['max_page_mae'], 0)
        self.assertGreater(report['cases'][0]['saved_bytes'], 0)
        self.assertGreaterEqual(report['cases'][0]['elapsed_ms'], 0)
        stored = json.loads((output / 'compression-benchmark-v50.4.json').read_text())
        self.assertEqual(stored['counts'], report['counts'])
        with fitz.open(output / report['cases'][0]['output_file']) as pdf:
            self.assertEqual(pdf.page_count, 1)
            self.assertIn('OpenPDF Studio', pdf[0].get_text())

    def test_existing_output_folder_refused_without_overwrite(self):
        out = self.root / 'benchmark'
        out.mkdir()
        sentinel = out / 'compression-benchmark-v50.4.json'
        sentinel.write_text('DO NOT REPLACE')
        with self.assertRaises(FileExistsError):
            benchmark_corpus([self.source], out)
        self.assertEqual(sentinel.read_text(), 'DO NOT REPLACE')

    def test_duplicate_sources_rejected_before_creating_folder(self):
        out = self.root / 'benchmark'
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            benchmark_corpus([self.source, self.source], out)
        self.assertFalse(out.exists())

    def test_invalid_pdf_rejected_as_failed_case(self):
        corrupt = self.root / 'corrupt.pdf'
        corrupt.write_bytes(b'%PDF-1.7\nnot-a-valid-pdf')
        report = benchmark_corpus([corrupt], self.root / 'benchmark',
                                  BenchmarkPolicy(profiles=('standard',)))
        self.assertEqual(report['counts']['rejected'], 1)
        self.assertEqual(report['cases'][0]['status'], 'rejected')
        self.assertFalse((self.root / 'benchmark' / report['cases'][0]['output_file']).exists())

    def test_invalid_profiles_and_budgets(self):
        for policy in (
            {'profiles': ('standard', 'standard')},
            {'profiles': ('bad',)},
            {'profiles': ()},
            {'render_scale': float('nan')},
            {'max_page_mae': True},
            {'max_inputs': True},
            {'max_input_bytes': 0},
            {'min_saving_percent': -1},
            {'min_saving_percent': float('nan')},
        ):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                BenchmarkPolicy(**policy)

    def test_symlink_input_refused_before_output(self):
        link = self.root / 'link.pdf'
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest('symlink unavailable')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            benchmark_corpus([link], self.root / 'benchmark')
        self.assertFalse((self.root / 'benchmark').exists())

    def test_source_size_budget_rejected_before_output(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            benchmark_corpus([self.source], self.root / 'benchmark',
                             BenchmarkPolicy(max_input_bytes=10))
        self.assertFalse((self.root / 'benchmark').exists())

    def test_rejected_engine_not_reported_as_success(self):
        with patch('openpdf_compression_benchmark_v504.execute_compression',
                   side_effect=RuntimeError('simulated engine failure')):
            report = benchmark_corpus([self.source], self.root / 'benchmark',
                                      BenchmarkPolicy(profiles=('standard',)))
        self.assertEqual(report['counts']['rejected'], 1)
        self.assertEqual(report['cases'][0]['error_type'], 'RuntimeError')
        self.assertNotIn('saving_percent', report['cases'][0])

    def test_minimum_saving_gate_rejects_before_publication(self):
        report = benchmark_corpus([self.source], self.root / 'benchmark',
                                  BenchmarkPolicy(profiles=('standard',), min_saving_percent=99.99))
        self.assertEqual(report['counts']['rejected'], 1)
        case = report['cases'][0]
        self.assertEqual(case['status'], 'rejected')
        self.assertFalse((self.root / 'benchmark' / case['output_file']).exists())

    def test_minimum_saving_gate_accepts_and_reports_full_rgb(self):
        report = benchmark_corpus([self.source], self.root / 'benchmark',
                                  BenchmarkPolicy(profiles=('standard',), min_saving_percent=1))
        self.assertEqual(report['counts']['published'], 1)
        self.assertEqual(report['cases'][0]['quality']['pixel_step'], 1)
        self.assertIn('full_rgb_pixels', report['cases'][0]['quality']['evidence'])
        self.assertGreater(report['cases'][0]['saving_percent'], 1)

    def test_cli_real_pdf(self):
        result = main([str(self.source), '--output-dir', str(self.root / 'benchmark'),
                       '--profiles', 'standard', '--strict'])
        self.assertEqual(result, 0)
        self.assertTrue((self.root / 'benchmark' / 'compression-benchmark-v50.4.json').exists())


if __name__ == '__main__':
    unittest.main()
