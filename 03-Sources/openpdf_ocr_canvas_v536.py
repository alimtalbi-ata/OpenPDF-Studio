"""V536: rotate OCR raster without silently clipping page-edge content.

A full-canvas Pillow rotation clips content at the corners. Rotate with an
expanded canvas, then uniformly fit (without anisotropic stretching) onto
an original-size white page. The source PDF remains unchanged. This is an
OCR pre-processing choice, not a fidelity or OCR-accuracy guarantee.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import math
from PIL import Image

MAX_CANVAS_PIXELS = 18_000_000


def rotate_ocr_canvas(image: Image.Image, angle_degrees: float, *,
                      max_pixels: int = MAX_CANVAS_PIXELS) -> Image.Image:
    """Return RGB raster with original dimensions and no rotation-edge crop.

    Nonzero rotation can reduce the effective text resolution to fit all
    original pixels. It never stretches the X and Y axes differently.
    """
    if (type(angle_degrees) not in (int, float) or
            not math.isfinite(angle_degrees) or abs(angle_degrees) > 12):
        raise ValueError('Angle de redressement OCR invalide [-12, 12]')
    if type(max_pixels) is not int or max_pixels <= 0:
        raise ValueError('Budget de pixels OCR invalide')
    width, height = image.size
    if width <= 0 or height <= 0 or width * height > max_pixels:
        raise ValueError('Budget de pixels OCR depasse')
    bitmap = image.convert('RGB')
    if angle_degrees == 0:
        return bitmap
    # Keep the original OCR resolution when foreground fits after rotation.
    # Only use full-canvas fitting when a normal rotation would clip content.
    mask = bitmap.convert('L').point(lambda value: 255 if value < 230 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return bitmap
    radians = math.radians(angle_degrees)
    cosine, sine = math.cos(radians), math.sin(radians)
    cx, cy = width / 2, height / 2
    left, top, right, bottom = bbox
    corners = ((left, top), (left, bottom), (right, top), (right, bottom))
    rotated_corners = [
        (cx + cosine * (x - cx) + sine * (y - cy),
         cy - sine * (x - cx) + cosine * (y - cy))
        for x, y in corners
    ]
    if all(2 <= x <= width - 2 and 2 <= y <= height - 2
           for x, y in rotated_corners):
        return bitmap.rotate(angle_degrees, resample=Image.Resampling.BICUBIC,
                             expand=False, fillcolor='white')
    rotated = bitmap.rotate(angle_degrees, resample=Image.Resampling.BICUBIC,
                            expand=True, fillcolor='white')
    # Fit the *whole* expanded image into the original page. Unlike a
    # non-expanded rotation, this retains content close to all four edges.
    scale = min(width / rotated.width, height / rotated.height, 1.0)
    target = (max(1, min(width, round(rotated.width * scale))),
              max(1, min(height, round(rotated.height * scale))))
    if rotated.size != target:
        rotated = rotated.resize(target, resample=Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (width, height), 'white')
    canvas.paste(rotated, ((width - target[0]) // 2,
                           (height - target[1]) // 2))
    return canvas
