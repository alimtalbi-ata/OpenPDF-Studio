"""Conservative, opt-in OCR selection for text/scanned hybrid PDFs.

V46.5: tiled scans are detected using *union* coverage, not the sum of image
areas (which double-counts overlays). Legacy bool policies remain unchanged.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations
from openpdf_ocr_union_v465 import visible_image_coverage, MAX_IMAGE_PLACEMENTS

SMART_TEXT_LIMIT = 80
SMART_IMAGE_COVERAGE = 0.65


def should_ocr_page(page, skip_text=True):
    """Return OCR decision; ``'smart'`` additionally handles tiled scans.

    A text-rich page remains untouched. Short text plus >=65% visible union
    image coverage triggers OCR. OCR rasterizes the whole page and may alter
    native vector content: this is an opt-in, conservative heuristic.
    """
    if type(skip_text) is bool:
        if not skip_text:
            return True
        return not bool(page.get_text('text').strip())
    if skip_text != 'smart':
        raise ValueError("Politique OCR invalide : True, False ou 'smart' attendus")
    text = page.get_text('text').strip()
    if not text:
        return True
    if len(text) > SMART_TEXT_LIMIT:
        return False
    return visible_image_coverage(page) >= SMART_IMAGE_COVERAGE
