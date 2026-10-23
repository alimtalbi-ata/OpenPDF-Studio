"""V50.7 independent page/pixel coverage check for compression receipts.

The RGB acceptance engine renders each page. This cheap second check reads the
actual source and candidate page geometry to ensure the claimed coverage is
complete, not merely a plausible number below the configured budget. It does
NOT repeat RGB rendering or certify print, OCR, accessibility, or PDF/A fidelity.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import math
from pathlib import Path


def verify_render_coverage(source, candidate, audit, policy):
    """Return independent coverage counts or reject before PDF publication.

    Pixel counts are computed from PyMuPDF's transformed page rectangle, the
    same raster bounds used by get_pixmap at the policy render scale. Neither
    input is modified; callers still verify hashes after this read-only check.
    """
    from openpdf_compression_acceptance_v489 import AcceptancePolicy
    if type(policy) is not AcceptancePolicy or type(audit) is not dict:
        raise TypeError('Expected an acceptance policy and a measured audit')
    import fitz
    left, right = Path(source), Path(candidate)
    if not left.is_file() or not right.is_file() or left.resolve() == right.resolve():
        raise RuntimeError('Distinct existing PDFs required for coverage check')
    try:
        with fitz.open(left) as original, fitz.open(right) as optimized:
            if original.needs_pass or optimized.needs_pass:
                raise RuntimeError('Encrypted PDF cannot be verified')
            pages = original.page_count
            if (not 1 <= pages <= policy.max_pages or pages != optimized.page_count
                    or type(audit.get('pages_compared')) is not int
                    or audit['pages_compared'] != pages):
                raise RuntimeError('RGB receipt does not cover every PDF page')
            transform = fitz.Matrix(policy.render_scale, policy.render_scale)
            pixels = 0
            for index in range(pages):
                before, after = original[index], optimized[index]
                geometry_before = (tuple(round(float(x), 4) for x in before.mediabox),
                                   tuple(round(float(x), 4) for x in before.cropbox),
                                   before.rotation)
                geometry_after = (tuple(round(float(x), 4) for x in after.mediabox),
                                  tuple(round(float(x), 4) for x in after.cropbox),
                                  after.rotation)
                if geometry_before != geometry_after:
                    raise RuntimeError(f'Page {index+1} geometry differs')
                bounds = before.rect
                if (bounds.is_empty or bounds.is_infinite or bounds.width <= 0
                        or bounds.height <= 0 or not math.isfinite(bounds.width * bounds.height)):
                    raise RuntimeError('Invalid PDF page geometry')
                raster = (bounds * transform).irect
                count = raster.width * raster.height
                if not 0 < count <= policy.max_pixels_per_page:
                    raise RuntimeError('Page raster exceeds pixel budget')
                pixels += count
                if pixels > policy.max_total_pixels:
                    raise RuntimeError('Raster coverage exceeds total pixel budget')
    except (ValueError, fitz.FileDataError) as exc:
        raise RuntimeError('Unreadable PDF during coverage verification') from exc
    if type(audit.get('pixels_compared')) is not int or audit['pixels_compared'] != pixels:
        raise RuntimeError('RGB receipt does not cover every rendered pixel')
    saving = left.stat().st_size - right.stat().st_size
    if type(audit.get('saved_bytes')) is not int or audit['saved_bytes'] != saving:
        raise RuntimeError('Compression saved-byte receipt disagrees with files')
    return {'pages_verified': pages, 'pixels_verified': pixels,
            'method': 'independent_pdf_page_geometry_not_second_raster_render'}
