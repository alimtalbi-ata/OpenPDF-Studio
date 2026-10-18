"""Isolated, atomic PDF operations. Author: Abdelhalim Talbi."""
from pathlib import Path
import os
import tempfile

class PDFOperationError(RuntimeError):
    pass

def _require_source(path):
    p = Path(path).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() != ".pdf":
        raise PDFOperationError(f"PDF source missing or invalid: {p}")
    return p

def _atomic_pdf(destination, writer, sources=()):
    target = Path(destination).expanduser().resolve()
    if target.suffix.lower() != ".pdf":
        raise PDFOperationError("Destination must have a .pdf extension")
    if target in {Path(s).resolve() for s in sources}:
        raise PDFOperationError("Refusing to overwrite an input PDF")
    if not target.parent.is_dir():
        raise PDFOperationError("Destination directory does not exist")
    fd, temp = tempfile.mkstemp(prefix=".openpdf-", suffix=".pdf", dir=target.parent)
    os.close(fd)
    try:
        writer(temp)
        if not Path(temp).is_file() or Path(temp).stat().st_size == 0:
            raise PDFOperationError("PDF writer produced an empty output")
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return target

def merge_pdfs(sources, destination):
    paths = [_require_source(p) for p in sources]
    if not paths:
        raise PDFOperationError("Select at least one source")
    import fitz
    def writer(temp):
        with fitz.open() as output:
            for path in paths:
                with fitz.open(path) as document:
                    if document.needs_pass:
                        raise PDFOperationError(f"Password required: {path.name}")
                    output.insert_pdf(document)
            output.save(temp, garbage=3, deflate=True)
    return _atomic_pdf(destination, writer, paths)

def extract_pages(source, destination, first, last):
    path = _require_source(source)
    if not isinstance(first, int) or not isinstance(last, int) or first < 1 or last < first:
        raise PDFOperationError("Invalid 1-based page range")
    import fitz
    def writer(temp):
        with fitz.open(path) as document:
            if document.needs_pass or last > len(document):
                raise PDFOperationError("Encrypted PDF or page range out of bounds")
            with fitz.open() as output:
                output.insert_pdf(document, from_page=first-1, to_page=last-1)
                output.save(temp, garbage=3, deflate=True)
    return _atomic_pdf(destination, writer, [path])
