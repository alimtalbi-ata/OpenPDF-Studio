"""V48.2: preserve PDF logical page labels through page operations.

Physical page indices and logical labels are different: a report may use i, ii,
1, 2, A-1, etc.  Copying pages with insert_pdf does not preserve /PageLabels.
This module plans the original labels per occurrence, remaps numbering, writes
PDF PageLabels and checks the *serialized* output before publication.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from bisect import bisect_right
from pathlib import Path

import fitz

MAX_PAGES = 20_000
MAX_LABEL_CHARS = 256
MAX_COUNTER = 1_000_000
STYLES = frozenset(('', 'D', 'r', 'R', 'a', 'A'))


def _expanded(doc):
    """Return (display, prefix, style, counter) for every source page."""
    rules = doc.get_page_labels()
    if len(rules) > doc.page_count:
        raise ValueError('Règles de numérotation PDF trop nombreuses')
    normalized = []
    starts = []
    for rule in rules:
        start = rule.get('startpage')
        prefix = rule.get('prefix', '')
        style = rule.get('style', '')
        first = rule.get('firstpagenum', 1)
        if (type(start) is not int or start < 0 or start >= doc.page_count
                or (starts and start <= starts[-1])
                or not isinstance(prefix, str) or len(prefix) > MAX_LABEL_CHARS
                or style not in STYLES or type(first) is not int
                or first < 1 or first > MAX_COUNTER):
            raise ValueError('Règle de numérotation PDF invalide')
        starts.append(start)
        normalized.append((prefix, style, first))
    result = []
    for index in range(doc.page_count):
        rule_index = bisect_right(starts, index) - 1
        if rule_index < 0:
            prefix, style, counter = '', '', 1
        else:
            prefix, style, first = normalized[rule_index]
            counter = first + index - starts[rule_index] if style else first
            if counter > MAX_COUNTER:
                raise ValueError('Compteur de numérotation PDF hors budget')
        display = doc[index].get_label()
        if not isinstance(display, str) or len(display) > MAX_LABEL_CHARS:
            raise ValueError('Libellé de page PDF hors budget')
        result.append((display, prefix, style, counter))
    return result


def prepare_label_plan(segments, *, max_pages=MAX_PAGES):
    """Capture labels for [(source_path, [one_based_pages]), ...] in output order."""
    if type(max_pages) is not int or max_pages < 1:
        raise ValueError('Budget de pages invalide')
    if not isinstance(segments, (tuple, list)) or not segments:
        raise ValueError('Segments de numérotation PDF invalides')
    plan = []
    for path, pages in segments:
        if (not isinstance(pages, (tuple, list)) or not pages
                or any(type(p) is not int for p in pages)):
            raise ValueError('Pages de numérotation PDF invalides')
        if len(plan) + len(pages) > max_pages:
            raise ValueError('Budget de pages numérotées dépassé')
        with fitz.open(str(Path(path))) as doc:
            if doc.needs_pass or not doc.page_count or any(p < 1 or p > doc.page_count for p in pages):
                raise ValueError('Source de numérotation PDF protégée ou hors limites')
            if doc.page_count > MAX_PAGES:
                raise ValueError('Budget de pages source PDF dépassé')
            expanded = _expanded(doc)
            plan.extend(expanded[p - 1] for p in pages)
    return tuple(plan)


def _rules(plan):
    result = []
    previous = None
    for index, (display, prefix, style, counter) in enumerate(plan):
        current = (prefix, style, counter)
        if (previous is None or prefix != previous[0] or style != previous[1]
                or (style and counter != previous[2] + 1)):
            result.append({'startpage': index, 'prefix': prefix,
                           'style': style, 'firstpagenum': counter})
        previous = current
    return result


def apply_label_plan(document, plan):
    """Set output page labels, without manufacturing labels for unlabeled PDFs."""
    if document.page_count != len(plan):
        raise RuntimeError('Nombre de pages PDF modifié avant numérotation')
    if not plan or not any(row[0] for row in plan):
        return
    document.set_page_labels(_rules(plan))


def verify_label_plan(document, plan):
    """Fail closed on lost labels or changed label numbering in saved output."""
    if document.page_count != len(plan):
        raise RuntimeError('Nombre de pages PDF modifié après numérotation')
    actual = _expanded(document)
    for got, expected in zip(actual, plan):
        if got[0] != expected[0]:
            raise RuntimeError('Libellé de page PDF perdu ou modifié')
        # Blank source pages may require a synthetic empty rule in a mixed PDF.
        if expected[0] and got[1:] != expected[1:]:
            raise RuntimeError('Style ou compteur de page PDF modifié')
