"""Optional, offline OCR service. Requires PyMuPDF and local Tesseract executable/data."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, os, tempfile, re
from openpdf_atomic_output import publish_exclusive

@dataclass(frozen=True)
class OCRReceipt:
    source: str
    destination: str
    pages: int
    ocr_pages: int
    skipped_pages: int
    sha256: str
    bytes_written: int
    language: str


def _digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def searchable_pdf(source, destination, language='fra+eng', dpi=200, skip_text=True, progress=None, tessdata=None):
    """Generate searchable PDF without modifying input; commit only complete valid output.

    Existing text pages are copied if skip_text=True; scanned pages OCR'd.
    progress is a callback (done,total); raising cancels before publication.
    """
    import fitz
    source=Path(source).expanduser().resolve(strict=True)
    destination=Path(destination).expanduser().resolve()
    if source==destination:raise ValueError('Source et destination identiques')
    if destination.exists():raise FileExistsError(f'Destination existante : {destination}')
    if not source.is_file() or source.stat().st_size==0:raise ValueError('Source vide ou invalide')
    if not destination.parent.is_dir():raise ValueError('Dossier de destination absent')
    if not re.fullmatch(r'[A-Za-z]{3}(?:\+[A-Za-z]{3})*',language):raise ValueError('Langue OCR invalide')
    if not isinstance(dpi,int) or not 100<=dpi<=400:raise ValueError('DPI hors limites [100,400]')
    if tessdata is not None and not Path(tessdata).is_dir():raise ValueError('Dossier tessdata absent')
    fd,tmp=tempfile.mkstemp(prefix='.openpdf-ocr-',suffix='.pdf',dir=destination.parent)
    os.close(fd)
    processed=0; skipped=0
    try:
        with fitz.open(source) as original, fitz.open() as result:
            if original.needs_pass:raise ValueError('PDF chiffré non pris en charge')
            if not original.page_count:raise ValueError('PDF sans page')
            for i,page in enumerate(original):
                if skip_text and page.get_text('text').strip():
                    result.insert_pdf(original,from_page=i,to_page=i)
                    skipped+=1
                else:
                    pix=page.get_pixmap(dpi=dpi,alpha=False)
                    kwargs={'language':language}
                    if tessdata is not None:kwargs['tessdata']=str(tessdata)
                    try:
                        pdf_bytes=pix.pdfocr_tobytes(**kwargs)
                    except RuntimeError as exc:
                        details=str(exc).lower()
                        if any(word in details for word in ('tessdata','tesseract','language','traineddata')):
                            raise RuntimeError(
                                'OCR indisponible : moteur Tesseract ou langues '
                                + language + ' manquants. Installez Tesseract OCR '
                                'avec les données de langue requises (fra et eng), '
                                'puis configurez TESSDATA_PREFIX vers le dossier tessdata.'
                            ) from exc
                        raise
                    with fitz.open(stream=pdf_bytes,filetype='pdf') as recognized:
                        result.insert_pdf(recognized)
                    processed+=1
                if progress:progress(i+1,original.page_count)
            if result.page_count!=original.page_count:raise RuntimeError('Nombre de pages incorrect')
            result.save(tmp,garbage=3,deflate=True)
        with fitz.open(tmp) as check:
            if check.page_count!=processed+skipped:raise RuntimeError('PDF OCR invalide')
        if Path(tmp).stat().st_size==0:raise RuntimeError('Sortie OCR vide')
        # Compute the receipt before publishing: an audit failure must not leave
        # a committed document with a failed operation result.
        digest = _digest(tmp)
        size = Path(tmp).stat().st_size
        publish_exclusive(tmp, destination)
        return OCRReceipt(str(source),str(destination),processed+skipped,processed,skipped,digest,size,language)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
