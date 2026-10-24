"""V535 opt-in, conservative raster deskew estimator (not OCR confidence).

The estimator uses only Pillow and operates on a bounded, downsampled image.
It never rotates native-text pages; the OCR service owns that safety gate.
No text is transmitted, and uncertain/photographic pages are left unchanged.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image


@dataclass(frozen=True)
class DeskewDecision:
    angle_degrees: float
    applied: bool
    reason: str
    projection_gain: float = 1.0


def estimate_deskew(image: Image.Image) -> DeskewDecision:
    """Return a *counter-rotation* angle, or a conservative no-op.

    This is a geometric alignment heuristic, not a claim of OCR accuracy.
    Scores concentration of foreground pixels into horizontal text lines.
    Rotation candidates are restricted to [-12, 12] degrees, with a
    0.25-degree refinement around the best integer candidate.
    """
    gray = image.convert('L')
    gray.thumbnail((900, 900), Image.Resampling.BILINEAR)
    width, height = gray.size
    if width < 100 or height < 100:
        return DeskewDecision(0.0, False, 'raster_too_small')
    # Dark foreground, white background. Thresholding prevents color
    # gradients from biasing the projection scores.
    mask = gray.point(lambda value: 255 if value < 185 else 0)
    dark = mask.tobytes().count(255)
    density = dark / (width * height)
    if dark < 150 or density < 0.001 or density > 0.18:
        return DeskewDecision(0.0, False, 'insufficient_text_like_pixels')

    def projection(angle: float):
        rotated = mask.rotate(angle, resample=Image.Resampling.NEAREST,
                              expand=False, fillcolor=0)
        data = rotated.tobytes()
        rows = [data[y * width:(y + 1) * width].count(255)
                for y in range(height)]
        total = sum(rows)
        return sum(count * count for count in rows) / max(total, 1), rows

    scores = {float(a): projection(float(a))[0] for a in range(-12, 13)}
    coarse = max(scores, key=scores.get)
    if abs(coarse) >= 12:
        return DeskewDecision(0.0, False, 'angle_outside_safe_window')
    for offset in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75):
        angle = coarse + offset
        scores[angle] = projection(angle)[0]
    best = max(scores, key=scores.get)
    peak = scores[best]
    baseline = max(scores[0.0], 1e-9)
    gain = peak / baseline
    if abs(best) < 0.75:
        return DeskewDecision(0.0, False, 'already_aligned', round(gain, 3))
    # Require a pronounced local maximum rather than a smooth preference
    # for rotating a photograph or a page containing only graphics.
    neighbors = max(projection(best - 2.0)[0], projection(best + 2.0)[0])
    _, rows = projection(best)
    threshold = max(rows) * 0.30
    bands = sum(value >= threshold and (index == 0 or rows[index - 1] < threshold)
                for index, value in enumerate(rows))
    if gain < 1.30 or peak / max(neighbors, 1e-9) < 1.15 or bands < 3:
        return DeskewDecision(0.0, False, 'ambiguous_text_alignment', round(gain, 3))
    return DeskewDecision(round(float(best), 2), True,
                          'projection_peak', round(gain, 3))
