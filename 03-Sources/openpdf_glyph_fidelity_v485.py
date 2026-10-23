"""V48.5 - fail-closed PDF glyph-layer fidelity for page transformations.

Detects changed whitespace, individual Unicode glyphs, font metadata, color,
opacity and glyph placement that word-based and low-resolution raster audits
can miss. This is a structural audit, not OCR accuracy or PDF/UA certification.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import math
from pathlib import Path
import fitz

MAX_PAGES = 20_000
MAX_GLYPHS_PER_PAGE = 100_000
MAX_GLYPHS_TOTAL = 1_000_000


def _finite_vector(values):
    if not isinstance(values, (tuple, list)) or not all(
        type(v) in (float, int) and math.isfinite(v) for v in values
    ):
        raise RuntimeError('Coordonnées de glyphe non vérifiables')
    return tuple(float(v) for v in values)


def _glyphs(page, page_number, limit):
    # PyMuPDF does not expose a streaming glyph extractor. These are logical
    # budgets checked after extraction, NOT hard process memory limits.
    raw = page.get_text('rawdict', sort=False)
    glyphs = []
    for block in raw.get('blocks', ()):
        if block.get('type') != 0:
            continue
        for line in block.get('lines', ()):
            for span in line.get('spans', ()):
                style = (span.get('font'), span.get('flags'),
                         span.get('char_flags'), span.get('color'),
                         span.get('alpha'), float(span.get('size', 0)))
                if not isinstance(style[0], str) or not math.isfinite(style[-1]):
                    raise RuntimeError(f'Style de texte invalide page {page_number}')
                for char in span.get('chars', ()):
                    if len(glyphs) >= limit:
                        raise ValueError(f'Budget de glyphes dépassé page {page_number}')
                    value = char.get('c')
                    if not isinstance(value, str) or len(value) != 1:
                        raise RuntimeError(f'Glyphe non vérifiable page {page_number}')
                    box = _finite_vector(char.get('bbox'))
                    origin = _finite_vector(char.get('origin'))
                    if (len(box) != 4 or len(origin) != 2
                            or box[0] > box[2] or box[1] > box[3]):
                        raise RuntimeError(f'Géométrie de glyphe invalide page {page_number}')
                    glyphs.append((value, box, origin, style,
                                   char.get('synthetic', False)))
    return glyphs


def validate_page_glyph_fidelity(segments, candidate, *, tolerance_pt=0.5,
                                 max_glyphs_per_page=MAX_GLYPHS_PER_PAGE,
                                 max_glyphs_total=MAX_GLYPHS_TOTAL):
    """Validate every mapped page occurrence before caller publishes output.

    segments: [(source_pdf, [1-based page numbers]), ...]. Duplicate pages
    are checked independently. Any unverifiable glyph fails closed.
    """
    if (type(tolerance_pt) not in (int, float) or not math.isfinite(tolerance_pt)
            or not 0 <= tolerance_pt <= 2):
        raise ValueError('Tolérance de glyphes invalide')
    if (type(max_glyphs_per_page) is not int or max_glyphs_per_page < 1
            or type(max_glyphs_total) is not int
            or max_glyphs_total < max_glyphs_per_page):
        raise ValueError('Budget de glyphes invalide')
    if not isinstance(segments, (tuple, list)) or not segments:
        raise ValueError('Plan de pages invalide')
    expected = 0
    for segment in segments:
        if not isinstance(segment, (tuple, list)) or len(segment) != 2:
            raise ValueError('Segment de pages invalide')
        pages = segment[1]
        if (not isinstance(pages, (tuple, list)) or not pages
                or any(type(p) is not int or p < 1 for p in pages)):
            raise ValueError('Indices de pages invalides')
        expected += len(pages)
        if expected > MAX_PAGES:
            raise ValueError('Budget de pages dépassé')
    candidate = Path(candidate).resolve(strict=True)
    total = 0
    empty_pages = 0
    with fitz.open(candidate) as output:
        if output.needs_pass or output.page_count != expected:
            raise RuntimeError('Pagination de sortie invalide')
        output_index = 0
        for source_path, pages in segments:
            source_path = Path(source_path).resolve(strict=True)
            if source_path == candidate:
                raise ValueError('Source et candidat identiques')
            with fitz.open(source_path) as source:
                if source.needs_pass or any(p > source.page_count for p in pages):
                    raise ValueError('Source protégée ou page invalide')
                for number in pages:
                    original = _glyphs(source[number - 1], number, max_glyphs_per_page)
                    actual = _glyphs(output[output_index], output_index + 1,
                                     max_glyphs_per_page)
                    if len(original) != len(actual):
                        raise RuntimeError(f'Nombre de glyphes modifié page {output_index + 1}')
                    total += len(original)
                    if total > max_glyphs_total:
                        raise ValueError('Budget total de glyphes dépassé')
                    if not original:
                        empty_pages += 1
                    for left, right in zip(original, actual):
                        if left[0] != right[0]:
                            raise RuntimeError(f'Texte glyphe modifié page {output_index + 1}')
                        if left[3] != right[3] or left[4] != right[4]:
                            raise RuntimeError(f'Style de glyphe modifié page {output_index + 1}')
                        if any(abs(a-b) > tolerance_pt for a,b in zip(left[1]+left[2],right[1]+right[2])):
                            raise RuntimeError(f'Position de glyphe modifiée page {output_index + 1}')
                    output_index += 1
    return {'pages_verified': expected, 'glyphs_verified': total,
            'pages_without_extractable_glyphs': empty_pages,
            'tolerance_pt': float(tolerance_pt),
            'method': 'mapped_rawdict_glyphs_style_and_coordinates',
            'limitation': 'not_ocr_accuracy_or_font_program_equivalence'}
