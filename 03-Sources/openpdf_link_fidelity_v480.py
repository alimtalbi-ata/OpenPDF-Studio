"""V48.0: fail-closed, page-aware PDF hyperlink fidelity.

Copying one PDF page at a time silently drops internal GOTO links in PyMuPDF.
This module rebuilds internal links with remapped page targets, preserves safe
external web/mail links and checks the serialized candidate before publication.
Unsupported actions and destinations to excluded pages are refused, not lost.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite
from pathlib import Path
from urllib.parse import urlsplit
import fitz

MAX_LINKS = 50_000
MAX_URI = 4096
ALLOWED_SCHEMES = frozenset(('https', 'http', 'mailto'))


def _rectangle(rect, bounds):
    values = tuple(float(v) for v in rect)
    if (len(values) != 4 or not all(isfinite(v) for v in values)
            or values[0] >= values[2] or values[1] >= values[3]
            or not fitz.Rect(values).intersects(bounds)):
        raise ValueError('Rectangle de lien PDF invalide')
    return values


def _point(point):
    if point is None:
        raise ValueError('Destination de lien PDF absente')
    values = tuple(float(v) for v in point)
    if len(values) != 2 or not all(isfinite(v) for v in values):
        raise ValueError('Destination de lien PDF invalide')
    return values


def _uri(value):
    if not isinstance(value, str) or not value or len(value) > MAX_URI:
        raise ValueError('URI de lien PDF invalide')
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError('Action de lien PDF externe non autorisée')
    if parsed.scheme.lower() in ('http', 'https') and not parsed.netloc:
        raise ValueError('Adresse de lien PDF invalide')
    return value


def prepare_link_plan(segments, *, max_links=MAX_LINKS):
    """Build a link plan for [(source_path, [1-based pages]), ...].

    A segment is an independent source occurrence (important when merging a
    document twice). A repeated target page maps to the first occurrence in
    its segment, except self-links, which map to the current output page.
    """
    if type(max_links) is not int or max_links < 1:
        raise ValueError('Budget de liens PDF invalide')
    if not isinstance(segments, (list, tuple)) or not segments:
        raise ValueError('Segments PDF invalides')
    plan = []
    link_count = 0
    for path, pages in segments:
        if not isinstance(pages, (list, tuple)) or not pages or any(type(p) is not int for p in pages):
            raise ValueError('Sélection de pages invalide')
        with fitz.open(str(Path(path))) as doc:
            if doc.needs_pass or not doc.page_count or any(p < 1 or p > doc.page_count for p in pages):
                raise ValueError('Source PDF protégée ou pages hors limites')
            if doc.embfile_count():
                raise ValueError('Pièces jointes PDF non préservées : opération refusée')
            if doc.is_form_pdf or doc.get_sigflags() > 0:
                raise ValueError('Formulaire ou signature PDF non préservé : opération refusée')
            positions = defaultdict(list)
            offset = len(plan)
            for index, page in enumerate(pages):
                positions[page - 1].append(offset + index)
            for index, number in enumerate(pages):
                output_page = offset + index
                source_page = doc[number - 1]
                links = []
                for link in source_page.get_links():
                    if link_count >= max_links:
                        raise ValueError('Budget de liens PDF dépassé')
                    rect = _rectangle(link['from'], source_page.rect)
                    kind = link.get('kind')
                    if kind == fitz.LINK_GOTO:
                        target = link.get('page')
                        if type(target) is not int or target not in positions:
                            raise ValueError('Lien vers une page exclue ou destination non prise en charge')
                        output_target = output_page if target == number - 1 else positions[target][0]
                        links.append(('goto', rect, output_target, _point(link.get('to'))))
                        link_count += 1
                    elif kind == fitz.LINK_URI:
                        links.append(('uri', rect, _uri(link.get('uri'))))
                        link_count += 1
                    else:
                        raise ValueError('Action de lien PDF non prise en charge : opération refusée')
                plan.append(tuple(links))
    return tuple(plan)


def apply_link_plan(document, plan):
    if document.page_count != len(plan):
        raise ValueError('Nombre de pages incompatible avec les liens PDF')
    for page_number, links in enumerate(plan):
        page = document[page_number]
        for link in links:
            if link[0] == 'goto':
                page.insert_link({'kind': fitz.LINK_GOTO, 'from': fitz.Rect(link[1]),
                                  'page': link[2], 'to': fitz.Point(link[3])})
            else:
                page.insert_link({'kind': fitz.LINK_URI, 'from': fitz.Rect(link[1]),
                                  'uri': link[2]})


def _close_tuple(left, right, tolerance=0.06):
    return len(left) == len(right) and all(abs(a - b) <= tolerance for a, b in zip(left, right))


def verify_link_plan(document, plan):
    """Check links on the reopened, serialized PDF; reject partial output."""
    if document.page_count != len(plan):
        raise RuntimeError('Nombre de pages des liens PDF modifié')
    for page_number, expected in enumerate(plan):
        actual = document[page_number].get_links()
        if len(actual) != len(expected):
            raise RuntimeError('Liens PDF manquants ou supplémentaires : sortie rejetée')
        for link, wanted in zip(actual, expected):
            if not _close_tuple(tuple(link['from']), wanted[1]):
                raise RuntimeError('Zone cliquable PDF modifiée : sortie rejetée')
            if wanted[0] == 'goto':
                if (link.get('kind') != fitz.LINK_GOTO or link.get('page') != wanted[2]
                        or not _close_tuple(tuple(link.get('to', ())), wanted[3])):
                    raise RuntimeError('Destination de lien interne modifiée : sortie rejetée')
            elif link.get('kind') != fitz.LINK_URI or link.get('uri') != wanted[2]:
                raise RuntimeError('URI de lien PDF modifiée : sortie rejetée')
