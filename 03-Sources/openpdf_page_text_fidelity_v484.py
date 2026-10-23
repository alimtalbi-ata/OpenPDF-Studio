"""V48.4 - text-layer fidelity for PDF page transformations.

Verify extractable words and coordinates for mapped source/output pages, even
when invisible text changes cannot be detected by a raster comparison.
This does not certify OCR accuracy, fonts, reading order or PDF/UA conformance.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import math
from pathlib import Path
import fitz

MAX_OUTPUT_PAGES = 20_000
MAX_WORDS_PER_PAGE = 50_000
MAX_WORDS_TOTAL = 500_000


def _words(page, page_number, max_words_per_page):
    words = page.get_text('words', sort=False)
    if len(words) > max_words_per_page:
        raise ValueError(f'Budget de mots dépassé page {page_number}')
    result = []
    for word in words:
        if len(word) < 5 or not isinstance(word[4], str):
            raise RuntimeError(f'Texte non vérifiable page {page_number}')
        box = tuple(float(value) for value in word[:4])
        if (not all(math.isfinite(value) for value in box)
                or box[0] > box[2] or box[1] > box[3]):
            raise RuntimeError(f'Coordonnées de texte invalides page {page_number}')
        result.append((word[4], box))
    return result


def validate_page_text_fidelity(segments, candidate, *, tolerance_pt=0.5,
                                max_words_per_page=MAX_WORDS_PER_PAGE,
                                max_words_total=MAX_WORDS_TOTAL):
    """Fail closed on changed text or word placement in transformed pages.

    segments: [(source_pdf, [1-based source page numbers]), ...]. Repeated
    sources and duplicated pages are intentionally verified each occurrence.
    The function only reads PDFs; caller must publish the candidate afterwards.
    """
    if (type(tolerance_pt) not in (int, float) or not math.isfinite(tolerance_pt)
            or not 0 <= tolerance_pt <= 2):
        raise ValueError('Tolérance géométrique invalide')
    if (type(max_words_per_page) is not int or max_words_per_page < 1
            or type(max_words_total) is not int
            or max_words_total < max_words_per_page):
        raise ValueError('Budget de mots invalide')
    if not isinstance(segments, (tuple, list)) or not segments:
        raise ValueError('Plan de pages invalide')
    expected = 0
    for segment in segments:
        if not isinstance(segment, (tuple, list)) or len(segment) != 2:
            raise ValueError('Segment de pages invalide')
        pages = segment[1]
        if (not isinstance(pages, (tuple, list)) or not pages
                or any(type(page) is not int or page < 1 for page in pages)):
            raise ValueError('Indices de pages invalides')
        expected += len(pages)
        if expected > MAX_OUTPUT_PAGES:
            raise ValueError('Budget de pages dépassé')
    candidate = Path(candidate).resolve(strict=True)
    total = 0
    blank = 0
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
                    raise ValueError('Source protégée ou index de page invalide')
                for number in pages:
                    source_words = _words(source[number-1], number, max_words_per_page)
                    output_words = _words(output[output_index], output_index+1, max_words_per_page)
                    if len(source_words) != len(output_words):
                        raise RuntimeError(f'Nombre de mots modifié page {output_index+1}')
                    total += len(source_words)
                    if total > max_words_total:
                        raise ValueError('Budget total de mots dépassé')
                    if not source_words:
                        blank += 1
                    for (text_a, rect_a), (text_b, rect_b) in zip(source_words, output_words):
                        if text_a != text_b:
                            raise RuntimeError(f'Texte modifié page {output_index+1}')
                        if any(abs(a-b) > tolerance_pt for a, b in zip(rect_a, rect_b)):
                            raise RuntimeError(f'Position du texte modifiée page {output_index+1}')
                    output_index += 1
    return {'pages_verified': expected, 'words_verified': total,
            'pages_without_extractable_words': blank,
            'tolerance_pt': float(tolerance_pt),
            'method': 'mapped_extracted_words_and_coordinates',
            'limitation': 'no_ocr_accuracy_or_hidden_text_semantics_certification'}
