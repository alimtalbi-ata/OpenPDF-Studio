"""Fail-closed OCR fidelity policy and round-trip audit.

Only document-level metadata, simple bookmarks, page labels and XMP are
copied. Features whose preservation cannot be demonstrated are rejected before
rasterization. This is deliberately not a PDF/UA or PDF/A certification.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations
from dataclasses import dataclass

_METADATA_KEYS = (
    'title', 'author', 'subject', 'keywords', 'creator', 'producer',
    'creationDate', 'modDate', 'trapped',
)


@dataclass(frozen=True)
class OCRDocumentProfile:
    metadata: dict
    bookmarks: list
    page_labels: list
    xmp: str


def _reject_complex_bookmarks(document):
    import fitz
    rich = document.get_toc(simple=False)
    for item in rich:
        if len(item) != 4:
            raise ValueError('Signets OCR non pris en charge')
        link = item[3]
        # Only plain internal GoTo bookmarks are reproducible with set_toc.
        if link.get('kind') != fitz.LINK_GOTO or link.get('page', -1) < 0:
            raise ValueError('Signets OCR avec action non prise en charge')
        if link.get('bold') or link.get('italic'):
            raise ValueError('Signets OCR stylisés non pris en charge')
        color = link.get('color')
        if color is not None and tuple(color) != (0.0, 0.0, 0.0):
            raise ValueError('Signets OCR colorés non pris en charge')


def preflight_ocr_document(document):
    """Reject features that would be silently dropped by a raster OCR rebuild."""
    if document.embfile_count() != 0:
        raise ValueError('OCR refusé : pièces jointes PDF non préservées')
    if document.is_form_pdf:
        raise ValueError('OCR refusé : formulaires PDF non préservés')
    if document.get_ocgs():
        raise ValueError('OCR refusé : calques PDF non préservés')
    _reject_complex_bookmarks(document)
    for number, page in enumerate(document, start=1):
        if page.get_links():
            raise ValueError(f'OCR refusé : liens PDF non préservés (page {number})')
        if page.first_annot is not None:
            raise ValueError(f'OCR refusé : annotations PDF non préservées (page {number})')
    raw = document.metadata or {}
    metadata = {key: raw[key] for key in _METADATA_KEYS if raw.get(key) is not None}
    return OCRDocumentProfile(metadata, document.get_toc(), document.get_page_labels(),
                              document.get_xml_metadata())


def apply_ocr_document_profile(result, profile):
    """Restore known-safe document-level semantics before saving."""
    if profile.metadata:
        result.set_metadata(profile.metadata)
    if profile.bookmarks:
        result.set_toc(profile.bookmarks)
    if profile.page_labels:
        result.set_page_labels(profile.page_labels)
    if profile.xmp:
        result.set_xml_metadata(profile.xmp)


def verify_ocr_document_profile(result, profile):
    """Check actual saved PDF, not just the in-memory intended values."""
    actual = result.metadata or {}
    for key, expected in profile.metadata.items():
        if actual.get(key) != expected:
            raise RuntimeError(f'Métadonnée OCR altérée : {key}')
    if result.get_toc() != profile.bookmarks:
        raise RuntimeError('Signets OCR altérés')
    if result.get_page_labels() != profile.page_labels:
        raise RuntimeError('Étiquettes de pages OCR altérées')
    if result.get_xml_metadata() != profile.xmp:
        raise RuntimeError('XMP OCR altéré')
