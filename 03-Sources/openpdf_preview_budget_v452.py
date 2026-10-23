"""Bound PDF preview raster allocation before calling PyMuPDF.

Author: Abdelhalim Talbi. V45.2.

This limits output pixel dimensions, not CPU time spent interpreting PDF
content; untrusted PDFs still require process-level resource isolation.
"""
from __future__ import annotations

import math

MAX_PREVIEW_PIXELS = 2_000_000
MAX_PREVIEW_PNG_BYTES = 8 * 1024 * 1024
MAX_TOTAL_PREVIEW_PNG_BYTES = 24 * 1024 * 1024


def safe_preview_scale(rect, *, preferred=0.7, max_pixels=MAX_PREVIEW_PIXELS):
    """Return a safe raster scale, or None for invalid/extreme geometry.

    Pixel dimensions are conservatively rounded up; 2% headroom prevents
    allocations just over the cap due to rasterizer rounding differences.
    """
    width, height = float(rect.width), float(rect.height)
    if not all(math.isfinite(v) and v > 0 for v in (width, height, preferred)):
        return None
    if type(max_pixels) is not int or max_pixels < 1:
        raise ValueError('max_pixels must be a positive integer')
    try:
        scale = min(preferred, math.sqrt(max_pixels / width / height) * 0.98)
    except (ValueError, OverflowError, ZeroDivisionError):
        return None
    if not math.isfinite(scale) or scale < 0.035:
        return None
    for _ in range(10):
        if math.ceil(width * scale) * math.ceil(height * scale) <= max_pixels:
            return scale
        scale *= 0.98
    return None
