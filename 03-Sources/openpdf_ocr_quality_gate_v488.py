"""Opt-in OCR acceptance gate; coverage is NOT recognition accuracy.
Author: Abdelhalim Talbi.
"""
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class OCRQualityPolicy:
    min_covered_fraction: float = 0.0
    min_characters_per_page: int = 0
    max_replacement_characters: int = 0

    def __post_init__(self):
        x = self.min_covered_fraction
        if type(x) not in (float, int) or not math.isfinite(x) or not 0 <= x <= 1:
            raise ValueError('Seuil de couverture OCR invalide [0,1]')
        for v in (self.min_characters_per_page, self.max_replacement_characters):
            if type(v) is not int or v < 0:
                raise ValueError('Seuil de caractères OCR invalide')


def evaluate_ocr_quality_gate(coverage, policy):
    if not isinstance(policy, OCRQualityPolicy):
        raise TypeError('Politique OCR invalide')
    n = coverage.ocr_pages
    receipts = coverage.page_receipts
    if type(n) is not int or n < 0 or len(receipts) != n:
        raise ValueError('Reçu de couverture OCR incohérent')
    if (coverage.ocr_pages_with_text + coverage.ocr_pages_without_text != n
            or coverage.ocr_pages_with_text < 0 or coverage.ocr_pages_without_text < 0):
        raise ValueError('Comptage des pages OCR incohérent')
    seen, counts = set(), []
    for r in receipts:
        if not isinstance(r, dict) or set(r) != {'page', 'characters', 'words'}:
            raise ValueError('Reçu de page OCR invalide')
        p, c, w = r['page'], r['characters'], r['words']
        if (type(p) is not int or not 1 <= p <= coverage.pages or p in seen
                or type(c) is not int or c < 0 or type(w) is not int or w < 0):
            raise ValueError('Reçu de page OCR incohérent')
        seen.add(p)
        counts.append(c)
    if sum(counts) != coverage.recognized_characters or sum(c > 0 for c in counts) != coverage.ocr_pages_with_text:
        raise ValueError('Reçu de couverture OCR altéré')
    fraction = sum(c > 0 for c in counts) / n if n else None
    if n and fraction + 1e-12 < policy.min_covered_fraction:
        raise ValueError('Qualité OCR refusée : couverture insuffisante')
    if any(c < policy.min_characters_per_page for c in counts):
        raise ValueError('Qualité OCR refusée : caractères insuffisants sur une page OCR')
    if (type(coverage.unicode_replacement_characters) is not int
            or coverage.unicode_replacement_characters < 0):
        raise ValueError('Comptage des caractères Unicode invalide')
    if coverage.unicode_replacement_characters > policy.max_replacement_characters:
        raise ValueError('Qualité OCR refusée : caractères Unicode de remplacement excessifs')
    return {'accepted': True, 'ocr_pages': n, 'covered_fraction': fraction,
            'policy': asdict(policy), 'evidence': 'measured_extractable_text_not_recognition_accuracy'}
