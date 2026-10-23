"""V51.3 model-integrity and real OCR tests. Windows binary is qualified in CI separately.
Author: Abdelhalim Talbi.
"""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
import openpdf_ocr_runtime_v513 as runtime
from openpdf_ocr_language_preflight_v486 import preflight_ocr_languages


class OCRRuntimeV513(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.bundle = self.root / 'bundle'
        self.models = self.bundle / 'tessdata'
        self.models.mkdir(parents=True)
        self.fake_eng = b'ENGLISH' * 300
        self.fake_fra = b'FRENCH' * 400
        (self.models / 'eng.traineddata').write_bytes(self.fake_eng)
        (self.models / 'fra.traineddata').write_bytes(self.fake_fra)
        self.pins = {
            'eng': (hashlib.sha256(self.fake_eng).hexdigest(), len(self.fake_eng)),
            'fra': (hashlib.sha256(self.fake_fra).hexdigest(), len(self.fake_fra)),
        }
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop('OPENPDF_TESSDATA_DIR', None)

    def resolve(self, language='eng+fra', **kwargs):
        with patch.object(runtime, 'BUNDLED_MODELS', self.pins):
            return runtime.resolve_ocr_models(language, frozen=True,
                                              bundle_root=self.bundle, **kwargs)

    def test_verified_bundle_both_languages(self):
        self.assertEqual(self.resolve(), self.models)

    def test_tampered_bundle_rejected(self):
        (self.models / 'eng.traineddata').write_bytes(b'X' * len(self.fake_eng))
        with self.assertRaisesRegex(RuntimeError, 'altere'):
            self.resolve()

    def test_missing_model_rejected(self):
        (self.models / 'fra.traineddata').unlink()
        with self.assertRaisesRegex(RuntimeError, 'absent'):
            self.resolve()

    def test_frozen_never_falls_back_to_system(self):
        with self.assertRaisesRegex(RuntimeError, 'integres absents'):
            runtime.resolve_ocr_models('eng', frozen=True,
                                       bundle_root=self.root / 'missing',
                                       executable=self.root / 'app.exe')

    def test_explicit_override_is_respected(self):
        other = self.root / 'external'
        other.mkdir()
        (other / 'eng.traineddata').write_bytes(self.fake_eng)
        self.assertEqual(self.resolve('eng', tessdata=other), other)

    def test_invalid_explicit_override_never_falls_back(self):
        with self.assertRaisesRegex(RuntimeError, 'absent'):
            self.resolve('eng', tessdata=self.root / 'absent')

    def test_environment_override(self):
        os.environ['OPENPDF_TESSDATA_DIR'] = str(self.models)
        self.assertEqual(self.resolve('eng'), self.models)

    def test_empty_environment_override_fails_closed(self):
        os.environ['OPENPDF_TESSDATA_DIR'] = ' '
        with self.assertRaisesRegex(RuntimeError, 'vide'):
            self.resolve('eng')

    def test_unknown_bundled_language_refused(self):
        (self.models / 'ita.traineddata').write_bytes(b'I' * 2000)
        with self.assertRaisesRegex(RuntimeError, 'non incluse'):
            self.resolve('ita')

    def test_symlink_model_refused(self):
        (self.models / 'eng.traineddata').unlink()
        try:
            (self.models / 'eng.traineddata').symlink_to(self.models / 'fra.traineddata')
        except OSError:
            self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(RuntimeError, 'symbolique'):
            self.resolve('eng')

    def test_invalid_language_refused(self):
        for language in ('../eng', 'eng;rm', '', 'en', 'ENG+fra/../../'):
            with self.subTest(language=language), self.assertRaises(ValueError):
                self.resolve(language)

    def test_real_ocr_from_system_models_if_available(self):
        try:
            preflight_ocr_languages('eng+fra')
        except (RuntimeError, ValueError, OSError):
            self.skipTest('Local eng+fra OCR models unavailable (not a Windows binary pass)')
        with patch.dict(os.environ, {'OPENPDF_TESSDATA_DIR': ''}, clear=False):
            os.environ.pop('OPENPDF_TESSDATA_DIR', None)
            receipt = runtime.functional_ocr_self_test()
        self.assertTrue(receipt['passed'])
        self.assertEqual(receipt['ocr_pages'], 1)
        self.assertTrue(receipt['output_sha256_verified'])
        self.assertFalse(receipt['accuracy_certified'])


if __name__ == '__main__':
    unittest.main()
