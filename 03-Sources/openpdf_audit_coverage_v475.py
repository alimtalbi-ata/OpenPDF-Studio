"""Verify the *coverage* of a compression visual audit without rerendering.

A digest and a zero-MAE value do not prove that all pages/pixels were sampled.
Reconstruct the exact raster dimensions that PyMuPDF uses for the configured
scale and verify the claimed page and pixel sample counts before publication.
This is a coverage check, not a visual-fidelity certification.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from pathlib import Path
import math
import fitz

MAX_AUDITED_PAGES = 500
MAX_AUDITED_PIXELS = 100_000_000


def verify_audit_coverage(audit, source, candidate):
    """Reject incomplete or fabricated audit coverage; return measured scope.

    The audit has already been validated for its data type and precision by the
    quality gate. This function never renders or modifies a PDF.
    """
    scale = audit.render_scale
    step = audit.sample_step
    if (isinstance(scale, bool) or not isinstance(scale, (int, float))
            or not math.isfinite(scale) or not 0.25 <= scale <= 2.0
            or type(step) is not int or not 1 <= step <= 32):
        raise RuntimeError('Paramètres de couverture visuelle invalides')
    src, dst = Path(source).resolve(), Path(candidate).resolve()
    if src == dst or not src.is_file() or not dst.is_file():
        raise RuntimeError('Deux fichiers PDF distincts sont requis pour la couverture')
    with fitz.open(src) as original, fitz.open(dst) as optimized:
        if original.needs_pass or optimized.needs_pass:
            raise RuntimeError('PDF protégé : couverture visuelle non vérifiable')
        count = original.page_count
        if not 1 <= count <= MAX_AUDITED_PAGES or optimized.page_count != count:
            raise RuntimeError('Couverture incomplète : pagination invalide')
        if type(audit.pages_compared) is not int or audit.pages_compared != count:
            raise RuntimeError('Couverture incomplète : pages non auditées')
        samples = 0
        rendered = 0
        matrix = fitz.Matrix(float(scale), float(scale))
        for index in range(count):
            before, after = original[index], optimized[index]
            for page in (before, after):
                rect = page.rect
                if (rect.is_empty or rect.is_infinite or rect.width <= 0
                        or rect.height <= 0):
                    raise RuntimeError(f'Géométrie non vérifiable page {index + 1}')
            if (tuple(before.mediabox) != tuple(after.mediabox)
                    or tuple(before.cropbox) != tuple(after.cropbox)
                    or before.rotation != after.rotation):
                raise RuntimeError(f'Géométrie modifiée page {index + 1}')
            bbox = (before.rect * matrix).irect
            width, height = int(bbox.width), int(bbox.height)
            if width < 1 or height < 1:
                raise RuntimeError(f'Rendu vide page {index + 1}')
            # Both source and candidate were rendered by the auditor.
            rendered += 2 * width * height
            if rendered > MAX_AUDITED_PIXELS:
                raise RuntimeError('Budget de couverture visuelle dépassé')
            samples += ((width + step - 1) // step) * ((height + step - 1) // step)
        if type(audit.pixels_sampled) is not int or audit.pixels_sampled != samples:
            raise RuntimeError('Couverture incomplète : nombre de pixels échantillonnés incorrect')
    return {'pages_verified': count, 'pixels_verified': samples,
            'evidence': 'exact_expected_render_sample_count_not_fidelity_certification'}
