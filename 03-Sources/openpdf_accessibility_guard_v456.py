"""Conservative accessibility metadata gate for PDF compression (V45.6).

Author: Abdelhalim Talbi.

PyMuPDF render/text checks cannot prove that a tagged PDF retains its
logical structure tree, reading order or assistive-technology semantics.
Until an independent structural validator is available, reject tagged input
rather than silently stripping accessibility information. For untagged input,
compare document/page language declarations and XMP metadata before publish.
This is a preservation gate, not a PDF/UA compliance certification.
"""

import hashlib
import re

_XREF = re.compile(r'^([1-9][0-9]*) 0 R$')
_MAX_PARENT_DEPTH = 64


def _key(doc, xref, name):
    kind, value = doc.xref_get_key(xref, name)
    if kind == 'null':
        return None
    if kind == 'string':
        return value
    # Do not silently treat malformed or indirect language values as absent.
    raise RuntimeError(f'Déclaration PDF /{name} non prise en charge')


def _ref(doc, xref, name):
    kind, value = doc.xref_get_key(xref, name)
    if kind == 'null':
        return None
    if kind != 'xref' or not _XREF.fullmatch(value):
        raise RuntimeError(f'Référence PDF /{name} non prise en charge')
    target = int(value.split(' ', 1)[0])
    if target >= doc.xref_length():
        raise RuntimeError(f'Référence PDF /{name} hors limites')
    return target


def _page_language(doc, page_index):
    """Capture language inherited through page tree, not just page dictionary."""
    xref = doc.page_xref(page_index)
    visited = set()
    for _ in range(_MAX_PARENT_DEPTH):
        if xref in visited:
            raise RuntimeError('Cycle dans les parents des pages PDF')
        visited.add(xref)
        lang = _key(doc, xref, 'Lang')
        if lang is not None:
            return lang
        xref = _ref(doc, xref, 'Parent')
        if xref is None:
            return None
    raise RuntimeError('Arborescence des pages PDF trop profonde')


def snapshot_accessibility(doc):
    """Fail closed on tagging and return stable, xref-independent metadata."""
    if doc.needs_pass:
        raise RuntimeError('PDF protégé : accessibilité non vérifiable')
    catalog = doc.pdf_catalog()
    # Even a seemingly empty tree may contain semantics that are invisible to
    # page rendering and extracted text. Do not claim preservation.
    for name in ('StructTreeRoot', 'MarkInfo'):
        kind, _ = doc.xref_get_key(catalog, name)
        if kind != 'null':
            raise RuntimeError('PDF balisé : conservation des tags non certifiable')
    for i in range(doc.page_count):
        kind, _ = doc.xref_get_key(doc.page_xref(i), 'StructParents')
        if kind != 'null':
            raise RuntimeError('PDF balisé : conservation des tags non certifiable')
    language = _key(doc, catalog, 'Lang')
    page_languages = tuple(_page_language(doc, i) for i in range(doc.page_count))
    xmp = doc.get_xml_metadata()
    if not isinstance(xmp, str):
        raise RuntimeError('Métadonnées XMP PDF non prises en charge')
    return (language, page_languages, hashlib.sha256(xmp.encode('utf-8')).hexdigest())


def reject_unverifiable_accessibility(doc):
    """Fast, conservative preflight for rewrite operations."""
    return snapshot_accessibility(doc)


def validate_accessibility_preserved(source, candidate):
    """Refuse changed language/XMP or tagged inputs without an adequate validator."""
    import fitz
    with fitz.open(str(source)) as original, fitz.open(str(candidate)) as output:
        if original.page_count != output.page_count:
            raise RuntimeError('Nombre de pages PDF modifié : sortie rejetée')
        if snapshot_accessibility(original) != snapshot_accessibility(output):
            raise RuntimeError('Langue/accessibilité/XMP PDF modifiés : sortie rejetée')
        return {'pages_verified': original.page_count,
                'accessibility_gate': 'untagged-metadata-preserved'}
