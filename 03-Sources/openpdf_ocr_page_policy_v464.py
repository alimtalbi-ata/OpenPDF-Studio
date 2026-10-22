"""Conservative OCR page selection for mixed scanned/text PDFs.

The opt-in ``skip_text='smart'`` policy prevents a short digital header from
hiding a full-page scan from OCR. It does not assert that OCR is necessary or
correct, and intentionally ignores small images and already text-rich pages.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations

SMART_TEXT_LIMIT = 80
SMART_IMAGE_COVERAGE = 0.65


def should_ocr_page(page, skip_text=True):
    """Return whether to rasterize a page for OCR.

    True/False retain the historic behaviour. The explicit ``'smart'`` mode
    additionally OCRs pages with <=80 extracted text characters and a single
    image covering >=65% of the visible page. This is intentionally a
    conservative heuristic, not an OCR quality assessment.
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

    # PyMuPDF exposes actual on-page image placements (including inline
    # images), unlike get_images() which may list unused XObjects.
    import fitz
    visible = fitz.Rect(page.rect)
    page_area = visible.get_area()
    if page_area <= 0:
        return False
    for item in page.get_image_info():
        bbox = item.get('bbox')
        if bbox is None:
            continue
        try:
            intersection = fitz.Rect(bbox) & visible
            if (not intersection.is_empty and
                    intersection.get_area() / page_area >= SMART_IMAGE_COVERAGE):
                return True
        except (ValueError, TypeError, OverflowError):
            continue
    return False
