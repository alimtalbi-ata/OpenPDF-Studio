"""V48.1: fail-closed preservation audit for common PDF review annotations.

PyMuPDF insert_pdf copies many annotations, but not every annotation subtype or
its linked objects (for example Text /Popup objects). Before any output is
published, this module compares the annotations on the *serialized* PDF with
those in the original source occurrences. It deliberately rejects annotations
whose full semantics cannot currently be guaranteed.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from math import isfinite
from pathlib import Path

import fitz

MAX_ANNOTATIONS = 50_000
MAX_TEXT = 16_384
MAX_VERTICES = 8_192
# PDF review markups supported by PyMuPDF insert_pdf (Text only without Popup).
SUPPORTED = frozenset({fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_HIGHLIGHT,
                       fitz.PDF_ANNOT_UNDERLINE, fitz.PDF_ANNOT_SQUIGGLY,
                       fitz.PDF_ANNOT_STRIKE_OUT})
# Linked/interactive payloads are not guaranteed by insert_pdf.
UNSUPPORTED_KEYS = frozenset({'Popup', 'IRT', 'RT', 'RC', 'A', 'AA', 'FS',
                              'Sound', 'Movie', 'RichMediaContent', '3DD', 'OC'})
INFO_FIELDS = ('content', 'name', 'title', 'subject', 'creationDate', 'modDate')


def _numbers(values):
    if values is None:
        return None
    if len(values) > MAX_VERTICES:
        raise ValueError('Géométrie annotation PDF trop volumineuse')
    result = tuple(float(v) for v in values)
    if not all(isfinite(v) for v in result):
        raise ValueError('Géométrie annotation PDF invalide')
    return result


def _signature(doc, annotation):
    if annotation.type[0] not in SUPPORTED:
        raise ValueError('Type annotation PDF non pris en charge : opération refusée')
    keys = set(doc.xref_get_keys(annotation.xref))
    for key in keys & UNSUPPORTED_KEYS:
        if doc.xref_get_key(annotation.xref, key)[0] != 'null':
            raise ValueError('Annotation PDF avec objet lié non préservé : ' + key)
    info = annotation.info
    fields = []
    for key in INFO_FIELDS:
        value = info.get(key) or ''
        if not isinstance(value, str) or len(value) > MAX_TEXT:
            raise ValueError('Métadonnée annotation PDF invalide')
        fields.append(value)
    rect = _numbers(tuple(annotation.rect))
    if rect[0] >= rect[2] or rect[1] >= rect[3]:
        raise ValueError('Rectangle annotation PDF invalide')
    vertices = annotation.vertices
    flattened_vertices = None
    if vertices is not None:
        if len(vertices) > MAX_VERTICES // 2:
            raise ValueError('Vertices annotation PDF hors budget')
        flattened_vertices = _numbers([n for vertex in vertices for n in vertex])
    colors = annotation.colors or {}
    stroke = _numbers(colors.get('stroke') or ())
    fill = _numbers(colors.get('fill') or ())
    opacity = float(annotation.opacity)
    if not isfinite(opacity) or not (opacity == -1 or 0 <= opacity <= 1):
        raise ValueError('Opacité annotation PDF invalide')
    return (annotation.type[0], rect, tuple(fields), int(annotation.flags),
            opacity, stroke, fill, flattened_vertices)


def prepare_annotation_plan(segments, *, max_annotations=MAX_ANNOTATIONS):
    """Capture annotation signatures in output page order.

    segments: [(source_path, [one_based_page_numbers]), ...]. Each occurrence
    is independent, including repeated pages or repeated source documents.
    """
    if type(max_annotations) is not int or max_annotations < 1:
        raise ValueError('Budget annotation PDF invalide')
    if not isinstance(segments, (tuple, list)) or not segments:
        raise ValueError('Segments annotations PDF invalides')
    plan = []
    total = 0
    for path, pages in segments:
        if not isinstance(pages, (tuple, list)) or not pages or any(type(p) is not int for p in pages):
            raise ValueError('Pages annotations PDF invalides')
        with fitz.open(str(Path(path))) as doc:
            if doc.needs_pass or not doc.page_count or any(p < 1 or p > doc.page_count for p in pages):
                raise ValueError('Source annotations PDF protégée ou hors limites')
            for page_number in pages:
                annotations = []
                for annot in doc[page_number - 1].annots() or ():
                    total += 1
                    if total > max_annotations:
                        raise ValueError('Budget annotations PDF dépassé')
                    annotations.append(_signature(doc, annot))
                plan.append(tuple(annotations))
    return tuple(plan)


def _near(left, right, tolerance=0.02):
    if left is None or right is None:
        return left is None and right is None
    return len(left) == len(right) and all(abs(a - b) <= tolerance for a, b in zip(left, right))


def verify_annotation_plan(document, plan):
    """Reject any lost/changed supported annotation in a serialized candidate."""
    if document.page_count != len(plan):
        raise RuntimeError('Nombre de pages annotations PDF modifié')
    for page_index, expected in enumerate(plan):
        actual = [_signature(document, annot) for annot in document[page_index].annots() or ()]
        if len(actual) != len(expected):
            raise RuntimeError('Annotations PDF perdues ou ajoutées : sortie rejetée')
        for found, wanted in zip(actual, expected):
            if (found[0] != wanted[0] or found[2:4] != wanted[2:4]
                    or not _near(found[1], wanted[1])
                    or abs(found[4] - wanted[4]) > 0.001
                    or not _near(found[5], wanted[5], 0.001)
                    or not _near(found[6], wanted[6], 0.001)
                    or not _near(found[7], wanted[7])):
                raise RuntimeError('Annotation PDF modifiée : sortie rejetée')
