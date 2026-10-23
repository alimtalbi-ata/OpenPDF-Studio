"""V48.3: bounded render-parity gate for PDF page transformations.

For every output page, render the corresponding source page at a fixed scale,
including visible annotations, and compare exact RGB pixel digests. This is a
low-resolution regression gate, not a guarantee of print-quality fidelity.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from math import isfinite
from pathlib import Path

import fitz

from openpdf_render_quality_v425 import _page_digest

MAX_OUTPUT_PAGES = 20_000
MAX_PAGE_PIXELS = 12_000_000
MAX_TOTAL_RENDER_PIXELS = 600_000_000


def _geometry(page):
    return (
        tuple(round(float(v), 4) for v in page.mediabox),
        tuple(round(float(v), 4) for v in page.cropbox),
        int(page.rotation),
    )


def _estimated_pixels(page, scale):
    rect = page.rect
    if not all(isfinite(v) for v in (rect.width, rect.height)):
        raise ValueError('Dimensions PDF non finies')
    width = int(rect.width * scale + 1)
    height = int(rect.height * scale + 1)
    if width < 1 or height < 1:
        raise ValueError('Dimensions PDF invalides')
    return width * height


def validate_page_visual_fidelity(
    segments, candidate, *, scale=0.5,
    max_page_pixels=MAX_PAGE_PIXELS,
    max_total_pixels=MAX_TOTAL_RENDER_PIXELS,
):
    """Check source-to-output page mapping before any candidate is published.

    ``segments`` is a sequence of ``(source_path, [one_based_pages])``. Each
    repeated occurrence is checked, including duplicated or reordered pages.
    All budget and page-index validation precedes expensive rendering.
    """
    if (isinstance(scale, bool) or not isinstance(scale, (float, int))
            or not isfinite(scale) or not 0.25 <= scale <= 1.0):
        raise ValueError('Echelle de rendu PDF invalide')
    if (type(max_page_pixels) is not int or max_page_pixels < 10_000
            or type(max_total_pixels) is not int
            or max_total_pixels < 2 * max_page_pixels):
        raise ValueError('Budget de rendu PDF invalide')
    if not isinstance(segments, (tuple, list)) or not segments:
        raise ValueError('Segments de rendu PDF invalides')
    if any(not isinstance(seg, (tuple, list)) or len(seg) != 2 for seg in segments):
        raise ValueError('Segment de rendu PDF invalide')
    count = 0
    for _, pages in segments:
        if (not isinstance(pages, (tuple, list)) or not pages
                or any(type(p) is not int for p in pages)):
            raise ValueError('Pages de rendu PDF invalides')
        count += len(pages)
        if count > MAX_OUTPUT_PAGES:
            raise ValueError('Budget de pages PDF dépassé')

    candidate = Path(candidate)
    with fitz.open(str(candidate)) as output:
        if output.needs_pass or output.page_count != count:
            raise RuntimeError('Nombre de pages de sortie modifié avant contrôle visuel')
        output_index = 0
        pixel_budget = 0
        for source_path, pages in segments:
            with fitz.open(str(Path(source_path))) as source:
                if (source.needs_pass or not source.page_count
                        or any(p < 1 or p > source.page_count for p in pages)):
                    raise ValueError('Source PDF protégée ou index de page invalide')
                for page_number in pages:
                    original = source[page_number - 1]
                    produced = output[output_index]
                    if _geometry(original) != _geometry(produced):
                        raise RuntimeError(
                            f'Géométrie PDF modifiée à la page {output_index + 1}')
                    pixels = _estimated_pixels(original, scale)
                    if pixels > max_page_pixels:
                        raise ValueError('Budget de pixels par page dépassé')
                    pixel_budget += 2 * pixels  # source + candidate raster
                    if pixel_budget > max_total_pixels:
                        raise ValueError('Budget de pixels cumulé dépassé')
                    source_digest = _page_digest(original, scale, max_page_pixels)
                    output_digest = _page_digest(produced, scale, max_page_pixels)
                    if source_digest != output_digest:
                        raise RuntimeError(
                            f'Rendu PDF modifié à la page {output_index + 1} : sortie rejetée')
                    output_index += 1
    return {
        'pages_verified': count,
        'scale': float(scale),
        'max_page_pixels': max_page_pixels,
        'raster_pixels_checked': pixel_budget,
        'method': 'exact_sha256_rgb_render_with_annotations',
        'limitation': 'low_resolution_sampling_not_print_fidelity_certification',
    }
