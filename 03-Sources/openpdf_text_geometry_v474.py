"""Fail-closed preservation of extractable text positions during PDF compression.

This is a lexical/layout check, not proof of font, visual, PDF/A or PDF/UA fidelity.
Coordinates are compared in PDF points with a configurable tolerance.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations
import math
from pathlib import Path

import fitz

MAX_PAGES = 2000
MAX_WORDS_PER_PAGE = 50000
MAX_WORDS_TOTAL = 500000


def _words(page, page_number):
    words = page.get_text('words', sort=False)
    if len(words) > MAX_WORDS_PER_PAGE:
        raise RuntimeError(f'Budget de mots dépassé page {page_number}')
    result = []
    for entry in words:
        if len(entry) < 5 or not isinstance(entry[4], str):
            raise RuntimeError(f'Extraction de texte non vérifiable page {page_number}')
        rect = tuple(float(x) for x in entry[:4])
        if not all(math.isfinite(x) for x in rect) or rect[0] > rect[2] or rect[1] > rect[3]:
            raise RuntimeError(f'Coordonnées de texte invalides page {page_number}')
        result.append((entry[4], rect))
    return result


def validate_text_geometry(source, candidate, *, tolerance_pt=0.5):
    """Check that all extracted words remain at their original page coordinates.

    Both documents are opened read-only. No file is modified. Raise on mismatch
    before a compressed candidate can be published.
    """
    if (isinstance(tolerance_pt, bool) or not isinstance(tolerance_pt, (int, float))
            or not math.isfinite(tolerance_pt) or not 0 <= tolerance_pt <= 2):
        raise ValueError('Tolérance géométrique du texte invalide')
    src, dst = Path(source).resolve(), Path(candidate).resolve()
    if src == dst or not src.is_file() or not dst.is_file():
        raise ValueError('Deux PDF distincts sont requis')
    checked = 0
    with fitz.open(src) as original, fitz.open(dst) as output:
        if original.needs_pass or output.needs_pass:
            raise RuntimeError('PDF protégé : vérification de texte impossible')
        count = original.page_count
        if not 1 <= count <= MAX_PAGES or count != output.page_count:
            raise RuntimeError('Pagination modifiée ou budget de pages dépassé')
        for i in range(count):
            before, after = _words(original[i], i+1), _words(output[i], i+1)
            if len(before) != len(after):
                raise RuntimeError(f'Nombre de mots modifié page {i+1} : sortie rejetée')
            checked += len(before)
            if checked > MAX_WORDS_TOTAL:
                raise RuntimeError('Budget total de mots dépassé : sortie rejetée')
            for (word_a, box_a), (word_b, box_b) in zip(before, after):
                if word_a != word_b:
                    raise RuntimeError(f'Texte modifié page {i+1} : sortie rejetée')
                if any(abs(a-b) > tolerance_pt for a, b in zip(box_a, box_b)):
                    raise RuntimeError(f'Position du texte modifiée page {i+1} : sortie rejetée')
    return {'pages_verified': count, 'words_verified': checked,
            'tolerance_pt': float(tolerance_pt),
            'evidence': 'extracted_word_coordinates_not_visual_certification'}
