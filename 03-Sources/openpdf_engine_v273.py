"""Cancellable PDF operations with progress and atomic publishing. Author: Abdelhalim Talbi."""
from openpdf_engine_v271 import _require_source, _atomic_pdf, PDFOperationError

def _check(cancelled):
    if cancelled is not None and cancelled():
        raise PDFOperationError("Opération annulée")

def _report(progress, fraction):
    if progress is not None:
        progress(max(0.0, min(1.0, float(fraction))))

def merge_pdfs(sources, destination, *, progress=None, cancelled=None):
    paths = [_require_source(p) for p in sources]
    if not paths: raise PDFOperationError("Sélectionnez au moins un PDF")
    import fitz
    def writer(temp):
        with fitz.open() as out:
            for i, path in enumerate(paths):
                _check(cancelled)
                with fitz.open(path) as doc:
                    if doc.needs_pass: raise PDFOperationError(f"Mot de passe requis : {path.name}")
                    out.insert_pdf(doc)
                _report(progress, (i+1)/(len(paths)+1))
            _check(cancelled)
            out.save(temp, garbage=3, deflate=True)
            _check(cancelled)
    result = _atomic_pdf(destination, writer, paths)
    _report(progress, 1)
    return result

def extract_pages(source, destination, first, last, *, progress=None, cancelled=None):
    path = _require_source(source)
    if not isinstance(first,int) or not isinstance(last,int) or first<1 or last<first:
        raise PDFOperationError("Plage de pages invalide")
    import fitz
    def writer(temp):
        with fitz.open(path) as doc:
            if doc.needs_pass or last>len(doc): raise PDFOperationError("PDF chiffré ou plage hors limites")
            with fitz.open() as out:
                count=last-first+1
                for i, page in enumerate(range(first-1,last)):
                    _check(cancelled)
                    out.insert_pdf(doc,from_page=page,to_page=page)
                    _report(progress,(i+1)/(count+1))
                _check(cancelled)
                out.save(temp,garbage=3,deflate=True)
                _check(cancelled)
    result=_atomic_pdf(destination,writer,[path]);_report(progress,1);return result

def compress_pdf(source,destination,*,progress=None,cancelled=None):
    path=_require_source(source)
    import fitz
    def writer(temp):
        _check(cancelled)
        with fitz.open(path) as doc:
            if doc.needs_pass: raise PDFOperationError("Mot de passe requis")
            _report(progress,0.2)
            _check(cancelled)
            doc.save(temp,garbage=4,deflate=True,deflate_images=True,deflate_fonts=True)
            _report(progress,0.9)
            _check(cancelled)
    result=_atomic_pdf(destination,writer,[path]);_report(progress,1);return result
