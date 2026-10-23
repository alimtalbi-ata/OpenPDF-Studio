"""V47.9: preserve internal bookmarks in extract/reorder/split operations.

No silent loss of attachments or unsupported destinations. For reordered or
repeated pages, bookmarks follow output page order and are flattened; a simple
ascending subset retains the available ancestor hierarchy. Only title and
page destination are promised (not zoom/scroll/view settings).
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from collections import defaultdict
import fitz

MAX_BOOKMARKS = 50_000


def prepare_page_navigation(source, page_numbers, *, max_bookmarks=MAX_BOOKMARKS):
    """Return output TOC for 1-based page numbers in output order.

    Reject unsupported navigation and embedded files before writing a candidate.
    """
    if type(max_bookmarks) is not int or max_bookmarks < 1:
        raise ValueError('Budget de signets invalide')
    if not isinstance(page_numbers, (tuple, list)) or not page_numbers or any(
        type(p) is not int for p in page_numbers
    ):
        raise ValueError('Sélection de pages invalide')
    with fitz.open(str(source)) as doc:
        if doc.needs_pass or not doc.page_count:
            raise ValueError('PDF source vide ou protégé')
        if any(p < 1 or p > doc.page_count for p in page_numbers):
            raise ValueError('Sélection de pages hors limites')
        if doc.embfile_count():
            raise ValueError('Pièces jointes PDF non préservées : opération refusée')
        if doc.is_form_pdf or doc.get_sigflags() > 0:
            raise ValueError('Formulaire ou signature PDF non préservé : opération refusée')
        entries = doc.get_toc(simple=True)
        if len(entries) > max_bookmarks:
            raise ValueError('Budget de signets PDF dépassé')
        locations = defaultdict(list)
        for out_page, source_page in enumerate(page_numbers, 1):
            locations[source_page].append(out_page)
        ascending = all(a < b for a, b in zip(page_numbers, page_numbers[1:]))
        selected = []
        original_ancestors = []
        parent_by_index = {}
        retained_levels = {}
        previous_level = 0
        for idx, entry in enumerate(entries):
            if len(entry) < 3:
                raise ValueError('Signet PDF invalide')
            level, title, page = entry[:3]
            if (type(level) is not int or level < 1 or level > previous_level + 1
                or not isinstance(title, str) or not title.strip()
                or type(page) is not int or not 1 <= page <= doc.page_count):
                raise ValueError('Signet PDF externe ou invalide : opération refusée')
            previous_level = level
            original_ancestors = original_ancestors[:level - 1]
            parent = original_ancestors[-1] if original_ancestors else None
            original_ancestors.append(idx)
            parent_by_index[idx] = parent
            if page not in locations:
                continue
            if ascending:
                while parent is not None and parent not in retained_levels:
                    parent = parent_by_index[parent]
                out_level = retained_levels[parent] + 1 if parent is not None else 1
                retained_levels[idx] = out_level
            else:
                out_level = 1
            for output_page in locations[page]:
                selected.append({'index': idx, 'parent': parent, 'toc': [out_level, title, output_page]})
            if len(selected) > max_bookmarks:
                raise ValueError('Budget de signets PDF dépassé')
        if not ascending:
            selected.sort(key=lambda item: (item['toc'][2], item['index']))
        return [item['toc'] for item in selected]


def apply_page_navigation(document, bookmarks):
    if bookmarks:
        document.set_toc(bookmarks, collapse=0)
    if document.get_toc(simple=True) != bookmarks:
        raise RuntimeError('Signets des pages modifiés : sortie rejetée')


def verify_page_navigation(document, bookmarks):
    if document.get_toc(simple=True) != bookmarks:
        raise RuntimeError('Signets du PDF sérialisé modifiés : sortie rejetée')
