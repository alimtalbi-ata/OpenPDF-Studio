"""Fail-closed native-text retention gate for hybrid-page OCR.

Any OCR-rasterized page with pre-existing extractable text is checked.
This is a lexical integrity control, NOT a guarantee of visual or semantic
fidelity, and it never claims to preserve vector glyphs or reading order.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations
import re
import unicodedata


def _words(value: str) -> tuple[str, ...]:
    if not isinstance(value, str):
        raise TypeError('Texte OCR invalide')
    return tuple(re.findall(r'\w+', unicodedata.normalize('NFKC', value).casefold(), re.UNICODE))


def assert_native_text_preserved(native_text: str, ocr_text: str, *, page: int) -> dict:
    """Require every original word to appear in OCR output in the same order.

    Extra OCR words are allowed (e.g. recognized text in a scanned image).
    Repeated native words require repeated output words. Punctuation, spacing
    and case are ignored; no fuzzy or fabricated matching is performed.
    """
    if type(page) is not int or page < 1:
        raise ValueError('Numéro de page OCR invalide')
    before = _words(native_text)
    after = _words(ocr_text)
    if not before:
        return {'page': page, 'native_words': 0, 'verified': True}
    cursor = iter(after)
    for token in before:
        if not any(word == token for word in cursor):
            raise RuntimeError(f'Texte natif perdu ou altéré pendant OCR intelligent (page {page})')
    return {'page': page, 'native_words': len(before), 'verified': True}
