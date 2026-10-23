"""Measured OCR text coverage and optional reference accuracy evaluation.

Coverage is observable text extraction, NOT an OCR accuracy certificate.
Reference CER/WER require caller-supplied ground truth. No network calls.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

MAX_AUDIT_CHARACTERS = 2_000_000
MAX_REFERENCE_CHARACTERS = 5_000
MAX_REFERENCE_WORDS = 1_000


@dataclass(frozen=True)
class OCRTextCoverage:
    pages: int
    ocr_pages: int
    ocr_pages_with_text: int
    ocr_pages_without_text: int
    recognized_characters: int
    recognized_words: int
    unicode_replacement_characters: int
    page_receipts: tuple
    evidence: str = 'text_coverage_only_not_recognition_accuracy'

    def to_dict(self):
        return asdict(self)


def audit_ocr_text_coverage(pdf, selected_pages, *, max_characters=MAX_AUDIT_CHARACTERS):
    """Inspect the *serialized* candidate before exclusive publication.

    `selected_pages` is one bool per page, True only for pages rasterized
    and OCR'd. A blank scan is valid: zero text is reported, not rejected.
    """
    if type(max_characters) is not int or max_characters < 1:
        raise ValueError('Budget de caractères OCR invalide')
    if not isinstance(selected_pages, (tuple, list)) or len(selected_pages) != pdf.page_count:
        raise ValueError('Sélection OCR incompatible avec le PDF produit')
    if any(type(flag) is not bool for flag in selected_pages):
        raise ValueError('Sélection OCR non booléenne')
    total_chars = total_words = replacements = nonempty = 0
    audited_codepoints = 0
    receipts = []
    for index, selected in enumerate(selected_pages):
        if not selected:
            continue
        text = pdf[index].get_text('text', sort=True)
        if not isinstance(text, str):
            raise RuntimeError('Extraction du texte OCR impossible')
        audited_codepoints += len(text)
        if audited_codepoints > max_characters:
            raise ValueError('Budget de caractères OCR dépassé')
        chars = sum(not c.isspace() for c in text)
        total_chars += chars
        words = len(text.split())
        total_words += words
        replacements += text.count('\ufffd')
        if text.strip():
            nonempty += 1
        receipts.append({'page': index + 1, 'characters': chars, 'words': words})
    return OCRTextCoverage(
        pdf.page_count, len(receipts), nonempty, len(receipts) - nonempty,
        total_chars, total_words, replacements, tuple(receipts))


def _edit_distance(a, b):
    """Levenshtein distance with linear memory; inputs are bounded by caller."""
    if len(a) < len(b):
        a, b = b, a
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        nxt = [i]
        for j, cb in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1,
                           row[j - 1] + (ca != cb)))
        row = nxt
    return row[-1]


def evaluate_reference_text(expected, recognized):
    """Compute CER and WER only against supplied ground truth.

    Returns None for an empty reference: accuracy cannot be estimated.
    Limits keep quadratic comparison bounded for desktop use.
    """
    if not isinstance(expected, str) or not isinstance(recognized, str):
        raise TypeError('Référence et reconnaissance doivent être du texte')
    reference = ' '.join(expected.split())
    actual = ' '.join(recognized.split())
    if not reference:
        return None
    if max(len(reference), len(actual)) > MAX_REFERENCE_CHARACTERS:
        raise ValueError('Référence OCR trop longue pour CER/WER')
    expected_words, actual_words = reference.split(), actual.split()
    if max(len(expected_words), len(actual_words)) > MAX_REFERENCE_WORDS:
        raise ValueError('Référence OCR trop longue en mots')
    return {'cer': round(_edit_distance(reference, actual) / len(reference), 6),
            'wer': round(_edit_distance(expected_words, actual_words) / len(expected_words), 6),
            'reference_characters': len(reference), 'reference_words': len(expected_words),
            'evidence': 'caller_supplied_ground_truth'}
