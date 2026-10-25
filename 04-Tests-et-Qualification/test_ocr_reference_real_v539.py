"""V539 real Tesseract OCR integration; synthetic-known reference, not human review.
Author: Abdelhalim Talbi.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_ocr_reference_corpus_v539 import SCHEMA, ANNOTATION_SCHEMA, evaluate_ocr_reference_corpus

@unittest.skipUnless(shutil.which('tesseract'), 'Real Tesseract executable not installed')
class RealTesseractOCRV539(unittest.TestCase):
    def test_two_real_ocr_pdf_conversions_with_synthetic_ground_truth(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = []
            for index, reference in enumerate(('OPENPDF OCR TEST 2026', 'STORAGE BACKUP REPORT 2027'), 1):
                with fitz.open() as doc:
                    page = doc.new_page(width=700, height=150)
                    page.insert_text((35, 95), reference, fontsize=28)
                    png = page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes('png')
                image = root / f'case-{index}.png'
                image.write_bytes(png)
                source = root / f'case-{index}-source.pdf'
                with fitz.open() as scanned:
                    page = scanned.new_page(width=700, height=150)
                    page.insert_image(page.rect, stream=png)
                    scanned.save(source)
                output_stem = root / f'case-{index}-ocr'
                process = subprocess.run(['tesseract', str(image), str(output_stem), '-l', 'eng', 'pdf'],
                                         capture_output=True, text=True, timeout=60)
                self.assertEqual(process.returncode, 0, process.stderr)
                output = output_stem.with_suffix('.pdf')
                self.assertTrue(output.is_file())
                annotation = root / f'case-{index}-annotation.json'
                annotation.write_text(json.dumps({
                    'schema': ANNOTATION_SCHEMA,
                    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'origin': 'synthetic_known_at_generation',
                    'pages': [{'page': 1, 'text': reference}],
                }), encoding='utf-8')
                cases.append({'id': f'case-{index}', 'source_pdf': source.name,
                              'ocr_pdf': output.name, 'annotations': annotation.name})
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({
                'schema': SCHEMA, 'cases': cases,
                'thresholds': {'max_cer': 0.1, 'max_wer': 0.25,
                               'max_case_cer': 0.2, 'max_case_wer': 0.3,
                               'min_human_reviewed': 0},
            }), encoding='utf-8')
            result = evaluate_ocr_reference_corpus(manifest)
            self.assertEqual(result['status'], 'PASS', result)
            self.assertEqual((result['cases'], result['pages']), (2, 2))
            self.assertEqual(result['human_reviewed_cases'], 0)
            self.assertLessEqual(result['cer'], 0.1)
            self.assertLessEqual(result['wer'], 0.25)

if __name__ == '__main__':
    unittest.main()
