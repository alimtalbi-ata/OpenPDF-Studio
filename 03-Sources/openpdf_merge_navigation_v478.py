"""V47.8: preserve basic internal PDF bookmarks during multi-document merge.

Source bookmarks are mapped to output page numbers; unsupported external or
named destinations and embedded attachments are rejected before output is
created, rather than being silently dropped. This intentionally preserves
navigation hierarchy, titles and target page numbers, not zoom/scroll offsets.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import fitz

MAX_BOOKMARKS = 50_000


def prepare_merge_navigation(paths, *, max_bookmarks=MAX_BOOKMARKS):
    """Return (bookmarks, pages) for source documents in the requested order."""
    if type(max_bookmarks) is not int or max_bookmarks < 1:
        raise ValueError('Budget de signets invalide')
    merged = []
    offset = 0
    for path in paths:
        with fitz.open(str(path)) as doc:
            if doc.needs_pass or not doc.page_count:
                raise ValueError('PDF source vide ou protégé')
            if doc.embfile_count():
                raise ValueError('Pièces jointes PDF non préservées : fusion refusée')
            entries = doc.get_toc(simple=True)
            if len(merged) + len(entries) > max_bookmarks:
                raise ValueError('Budget de signets PDF dépassé')
            previous_level = 0
            for entry in entries:
                if len(entry) < 3:
                    raise ValueError('Signet PDF invalide')
                level, title, page = entry[:3]
                if (type(level) is not int or level < 1 or
                        level > previous_level + 1 or
                        not isinstance(title, str) or not title.strip() or
                        type(page) is not int or not 1 <= page <= doc.page_count):
                    raise ValueError('Signet PDF non interne ou invalide : fusion refusée')
                merged.append([level, title, offset + page])
                previous_level = level
            offset += doc.page_count
    return merged, offset


def apply_merge_navigation(document, bookmarks):
    """Apply and verify the page-level navigation tree before saving."""
    if not bookmarks:
        return
    document.set_toc(bookmarks, collapse=0)
    if document.get_toc(simple=True) != bookmarks:
        raise RuntimeError('Les signets de fusion ne correspondent pas au plan')


def verify_merge_navigation(document, bookmarks):
    """Verify the *serialized* candidate before exclusive publication."""
    if document.get_toc(simple=True) != bookmarks:
        raise RuntimeError('Signets du PDF produit modifiés : sortie rejetée')
