"""Lossless, bounded pagination of extracted PDF text into editable PPTX slides.

The text is the extractable PyMuPDF text, not a reconstruction of PDF layout.
No text is silently truncated: overly large pages fail explicitly.
Author: Abdelhalim Talbi.
"""

MAX_CHARS_PER_SLIDE = 650
MAX_LINES_PER_SLIDE = 18
MAX_SLIDES_PER_PDF_PAGE = 500


def split_text_for_slides(text, *, max_chars=MAX_CHARS_PER_SLIDE,
                          max_lines=MAX_LINES_PER_SLIDE):
    """Yield consecutive fragments whose concatenation equals *text* exactly.

    A newline is included in the preceding fragment whenever possible. Limits
    apply to Python Unicode codepoints and explicit lines, not visual glyphs.
    """
    if not isinstance(text, str):
        raise TypeError('Le texte extrait doit etre une chaine')
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 1:
        raise ValueError('Limite de caracteres invalide')
    if not isinstance(max_lines, int) or isinstance(max_lines, bool) or max_lines < 1:
        raise ValueError('Limite de lignes invalide')
    if not text:
        yield ''
        return

    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        candidate = text[start:end]
        # Do not place more than max_lines explicit lines on one slide.
        offset = 0
        for _ in range(max_lines):
            at = candidate.find('\n', offset)
            if at < 0:
                break
            offset = at + 1
        if offset and candidate.find('\n', offset) >= 0:
            end = start + offset
        elif end < len(text):
            # Prefer the last complete line in the second half of the chunk.
            at = candidate.rfind('\n', max_chars // 2)
            if at >= 0:
                end = start + at + 1
        if end <= start:
            raise RuntimeError('Pagination PowerPoint sans progression')
        yield text[start:end]
        start = end


def chunks_for_page(text):
    """Materialize only one PDF page; reject resource exhaustion, never trim."""
    chunks = []
    for chunk in split_text_for_slides(text):
        if len(chunks) >= MAX_SLIDES_PER_PDF_PAGE:
            raise ValueError('Page PDF trop volumineuse pour PowerPoint : '
                             'export annule sans troncature')
        chunks.append(chunk)
    return chunks
