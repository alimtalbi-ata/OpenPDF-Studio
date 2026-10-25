"""V537 OCR raster resolution regression: executable synthetic-image tests.

Synthetic images are NOT independent OCR accuracy ground truth.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import sys
import unittest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_ocr_canvas_v536 import rotate_ocr_canvas


def dark_pixels(image):
    return image.convert('L').point(lambda v: 1 if v < 160 else 0).tobytes().count(1)


def legacy_full_canvas_fit(image, angle):
    rotated = image.convert('RGB').rotate(angle, resample=Image.Resampling.BICUBIC,
                                          expand=True, fillcolor='white')
    width, height = image.size
    scale = min(width / rotated.width, height / rotated.height, 1.0)
    target = (round(rotated.width * scale), round(rotated.height * scale))
    rotated = rotated.resize(target, Image.Resampling.LANCZOS)
    result = Image.new('RGB', (width, height), 'white')
    result.paste(rotated, ((width - target[0]) // 2, (height - target[1]) // 2))
    return result


class ForegroundFitV537(unittest.TestCase):
    def test_localized_corner_content_retains_more_character_pixels(self):
        image = Image.new('RGB', (800, 500), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((1, 1, 35, 35), fill='black')
        draw.rectangle((350, 200, 400, 230), fill='black')
        baseline = legacy_full_canvas_fit(image, -12)
        actual = rotate_ocr_canvas(image, -12)
        self.assertEqual(actual.size, image.size)
        self.assertGreater(dark_pixels(actual), dark_pixels(baseline) * 1.4)

    def test_four_corner_content_is_not_dropped(self):
        image = Image.new('RGB', (800, 500), 'white')
        draw = ImageDraw.Draw(image)
        for x in (2, 740):
            for y in (2, 440):
                draw.rectangle((x, y, x + 55, y + 55), fill='black')
        actual = rotate_ocr_canvas(image, -12)
        self.assertEqual(actual.size, image.size)
        self.assertGreater(dark_pixels(actual), 6500)

    def test_source_raster_is_not_modified(self):
        image = Image.new('RGB', (800, 500), 'white')
        ImageDraw.Draw(image).rectangle((1, 1, 70, 70), fill='black')
        before = image.tobytes()
        actual = rotate_ocr_canvas(image, -12)
        self.assertEqual(image.tobytes(), before)
        self.assertIsNot(actual, image)

    def test_centered_text_retains_legacy_resolution(self):
        image = Image.new('RGB', (800, 500), 'white')
        ImageDraw.Draw(image).rectangle((250, 170, 550, 330), fill='black')
        expected = image.rotate(-8, resample=Image.Resampling.BICUBIC,
                                expand=False, fillcolor='white')
        self.assertEqual(rotate_ocr_canvas(image, -8).tobytes(), expected.tobytes())

    def test_safety_checks_still_reject_oversized_input(self):
        image = Image.new('RGB', (800, 500), 'white')
        with self.assertRaisesRegex(ValueError, 'Budget'):
            rotate_ocr_canvas(image, -8, max_pixels=1000)


if __name__ == '__main__':
    unittest.main()
