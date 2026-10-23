"""Bounded OCR work planning before any PDF page is rasterized.

The planner counts only pages selected for OCR, so text-only pages copied
unchanged do not consume the OCR budget. Failures are explicit; no page is
silently downsampled or skipped to fit the budget.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import math

MAX_OCR_PIXELS_PER_PAGE = 18_000_000
DEFAULT_TOTAL_OCR_PIXELS = 1_000_000_000
DEFAULT_OCR_PAGES = 500


def plan_ocr_pages(document, dpi, select_page, *,
                   max_total_pixels=DEFAULT_TOTAL_OCR_PIXELS,
                   max_ocr_pages=DEFAULT_OCR_PAGES):
    """Return ``(selected_pages, audit)`` before starting expensive OCR.

    ``select_page`` is called once per page; its truth value determines if the
    page will be rasterized. Both page count and cumulative pixel budgets are
    checked *before* the caller processes any selected page. The per-page
    limit is a separate hard cap against a single excessive allocation.
    """
    if type(dpi) is not int or not 100 <= dpi <= 400:
        raise ValueError('DPI OCR invalide [100,400]')
    if type(max_total_pixels) is not int or max_total_pixels < 1:
        raise ValueError('Budget total OCR invalide')
    if type(max_ocr_pages) is not int or max_ocr_pages < 1:
        raise ValueError('Budget de pages OCR invalide')
    if not callable(select_page):
        raise TypeError('Sélecteur de pages OCR invalide')

    decisions = []
    total_pixels = 0
    count = 0
    for number, page in enumerate(document, 1):
        selected = bool(select_page(page))
        if selected:
            width, height = float(page.rect.width), float(page.rect.height)
            if not all(math.isfinite(v) and v > 0 for v in (width, height)):
                raise ValueError(f'Géométrie OCR invalide (page {number})')
            pixels_w = math.ceil(width * dpi / 72)
            pixels_h = math.ceil(height * dpi / 72)
            pixels = pixels_w * pixels_h
            if pixels > MAX_OCR_PIXELS_PER_PAGE:
                raise ValueError(f'Budget OCR par page dépassé : limite de pixels (page {number})')
            count += 1
            if count > max_ocr_pages:
                raise ValueError(f'Budget de pages OCR dépassé (page {number})')
            if pixels > max_total_pixels - total_pixels:
                raise ValueError(f'Budget total de pixels OCR dépassé (page {number})')
            total_pixels += pixels
        decisions.append(selected)
    return tuple(decisions), {'ocr_pages': count,
                              'estimated_pixels': total_pixels,
                              'max_ocr_pages': max_ocr_pages,
                              'max_total_pixels': max_total_pixels}
