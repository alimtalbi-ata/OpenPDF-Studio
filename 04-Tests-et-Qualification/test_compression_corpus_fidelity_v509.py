"""V50.9 real PDF corpus safety and measurement regression.
Synthetic fixtures only. Author: Abdelhalim Talbi.
"""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_compression_benchmark_v504 import BenchmarkPolicy, benchmark_corpus


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CorpusFidelityV509(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = self.root / 'transparency.pdf'
        with fitz.open() as doc:
            page = doc.new_page(width=250, height=180)
            page.draw_rect(fitz.Rect(25, 25, 170, 100), fill=(0, 0.8, 0.2),
                           fill_opacity=0.5, color=None)
            page.insert_text((30, 130), 'Transparent PDF quality')
            doc.set_metadata({'title': 'V50.9 transparency corpus'})
            doc.save(self.source, deflate=False)
        with self.source.open('ab') as stream:
            stream.write(b' ' * 6000)

    def test_real_corpus_rgb_alpha_coverage_and_weighted_saving(self):
        source_sha = digest(self.source)
        report = benchmark_corpus([self.source], self.root / 'results',
                                  BenchmarkPolicy(profiles=('standard', 'smaller_only')))
        self.assertEqual(report['verification'], 'v50.9-rgb-coverage-alpha-sha256')
        self.assertEqual(report['counts']['published'], 2, report['cases'])
        for case in report['cases']:
            self.assertGreaterEqual(case['process_cpu_ms'], 0)
            self.assertGreaterEqual(case['elapsed_ms'], 0)
            self.assertEqual(case['source_sha256'], source_sha)
            quality = case['quality']
            self.assertEqual(quality['alpha']['alpha_mismatch_pixels'], 0)
            self.assertGreater(quality['alpha']['translucent_pixels'], 0)
            self.assertEqual(quality['coverage']['pages_verified'], 1)
            self.assertEqual(quality['coverage']['pixels_verified'], quality['alpha']['pixels_verified'])
            self.assertEqual(quality['pixels_compared'], quality['alpha']['pixels_verified'])
            self.assertEqual(quality['alpha']['candidate_sha256'], case['output_sha256'])
            self.assertEqual(digest(self.root / 'results' / case['output_file']), case['output_sha256'])
            summary = report['by_profile'][case['profile']]
            self.assertEqual(summary['accepted_saved_bytes'], case['saved_bytes'])
            self.assertEqual(summary['published'], 1)
            self.assertAlmostEqual(summary['weighted_saving_percent'], case['saving_percent'], places=4)
        self.assertEqual(digest(self.source), source_sha)
        stored = json.loads((self.root / 'results' / 'compression-benchmark-v50.4.json').read_text())
        self.assertEqual(stored['by_profile'], report['by_profile'])

    def test_alpha_mismatch_rejects_and_removes_output(self):
        with patch('openpdf_compression_benchmark_v504.verify_alpha_fidelity',
                   side_effect=RuntimeError('injected alpha mismatch')):
            report = benchmark_corpus([self.source], self.root / 'results',
                                      BenchmarkPolicy(profiles=('standard',)))
        case = report['cases'][0]
        self.assertEqual(case['status'], 'rejected')
        self.assertIn('alpha mismatch', case['error'])
        self.assertFalse((self.root / 'results' / case['output_file']).exists())
        self.assertIsNone(report['by_profile']['standard']['weighted_saving_percent'])

    def test_coverage_mismatch_rejects_and_removes_output(self):
        with patch('openpdf_compression_benchmark_v504.verify_render_coverage',
                   side_effect=RuntimeError('injected RGB coverage mismatch')):
            report = benchmark_corpus([self.source], self.root / 'results',
                                      BenchmarkPolicy(profiles=('standard',)))
        self.assertEqual(report['counts']['rejected'], 1)
        self.assertFalse((self.root / 'results' / report['cases'][0]['output_file']).exists())

    def test_forged_alpha_pixel_count_fails_closed(self):
        with patch('openpdf_compression_benchmark_v504.verify_alpha_fidelity',
                   return_value={'pixels_verified': 1, 'alpha_mismatch_pixels': 0}):
            report = benchmark_corpus([self.source], self.root / 'results',
                                      BenchmarkPolicy(profiles=('standard',)))
        self.assertEqual(report['counts']['rejected'], 1)
        self.assertIn('coverage mismatch', report['cases'][0]['error'])
        self.assertFalse((self.root / 'results' / report['cases'][0]['output_file']).exists())

    def test_strict_saving_threshold_still_fails_closed(self):
        report = benchmark_corpus([self.source], self.root / 'results',
                                  BenchmarkPolicy(profiles=('standard',), min_saving_percent=99.99))
        self.assertEqual(report['counts']['rejected'], 1)
        self.assertEqual(report['by_profile']['standard']['published'], 0)
        self.assertFalse((self.root / 'results' / report['cases'][0]['output_file']).exists())

    def test_existing_folder_preflight(self):
        output = self.root / 'results'
        output.mkdir()
        (output / 'sentinel').write_text('untouched')
        with self.assertRaises(FileExistsError):
            benchmark_corpus([self.source], output)
        self.assertEqual((output / 'sentinel').read_text(), 'untouched')


if __name__ == '__main__':
    unittest.main()
