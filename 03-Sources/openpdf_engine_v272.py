"""V27.2 safe PDF operations; author Abdelhalim Talbi."""
from pathlib import Path
from openpdf_engine_v271 import _require_source, _atomic_pdf, PDFOperationError, merge_pdfs, extract_pages

def compress_pdf(source, destination, *, progress=None, cancelled=None):
    """Lossless structural compression; size reduction is not guaranteed."""
    source = _require_source(source)
    import fitz
    def writer(temp):
        if cancelled and cancelled():
            raise PDFOperationError('Operation cancelled')
        with fitz.open(source) as doc:
            if doc.needs_pass:
                raise PDFOperationError('Password required')
            if progress: progress(0.3)
            doc.save(temp, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True)
        if cancelled and cancelled():
            raise PDFOperationError('Operation cancelled')
        if progress: progress(1.0)
    return _atomic_pdf(destination, writer, [source])
