"""Exact, bounded visible image union coverage for OCR page selection.

Author: Abdelhalim Talbi. No OCR is executed by this module.
"""
from __future__ import annotations
import math
MAX_IMAGE_PLACEMENTS = 512

def visible_image_coverage(page):
    """Exact union fraction of clipped image rectangles; no double-counting.

    Rectangles are display placements reported by PyMuPDF, not unused XObjects.
    A bounded sweep avoids memory/CPU surprises from pathological PDF pages.
    """
    import fitz
    visible = fitz.Rect(page.rect)
    page_area = visible.get_area()
    if not math.isfinite(page_area) or page_area <= 0:
        raise ValueError('Géométrie de page OCR invalide')
    placements = page.get_image_info()
    if len(placements) > MAX_IMAGE_PLACEMENTS:
        raise ValueError('Trop de placements image pour une décision OCR fiable')
    rects = []
    for item in placements:
        bbox = item.get('bbox')
        if bbox is None:
            continue
        try:
            if len(bbox) != 4 or not all(math.isfinite(float(v)) for v in bbox):
                continue
            rect = fitz.Rect(bbox) & visible
            if not rect.is_empty and rect.get_area() > 0:
                rects.append((rect.x0, rect.y0, rect.x1, rect.y1))
        except (ValueError, TypeError, OverflowError):
            continue
    if not rects:
        return 0.0
    xs = sorted({x for left, _, right, _ in rects for x in (left, right)})
    area = 0.0
    for x0, x1 in zip(xs, xs[1:]):
        if x1 <= x0:
            continue
        spans = sorted((y0, y1) for left, y0, right, y1 in rects
                       if left < x1 and right > x0)
        if not spans:
            continue
        low, high = spans[0]
        covered = 0.0
        for y0, y1 in spans[1:]:
            if y0 <= high:
                high = max(high, y1)
            else:
                covered += high - low
                low, high = y0, y1
        covered += high - low
        area += (x1 - x0) * covered
    return min(1.0, max(0.0, area / page_area))

