"""Optional, offline OCR service. Requires PyMuPDF and local Tesseract executable/data."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, os, tempfile, re, math
from openpdf_source_integrity_v430 import fingerprint_source, verify_source_unchanged
from openpdf_atomic_output import publish_exclusive
from openpdf_ocr_page_policy_v464 import should_ocr_page
from openpdf_ocr_native_text_v466 import assert_native_text_preserved
from openpdf_ocr_budget_v467 import (plan_ocr_pages, DEFAULT_TOTAL_OCR_PIXELS, DEFAULT_OCR_PAGES)
from openpdf_ocr_fidelity_v463 import (preflight_ocr_document,
    apply_ocr_document_profile, verify_ocr_document_profile)

MAX_OCR_PIXELS = 18_000_000


def validate_ocr_raster(page, dpi, *, max_pixels=MAX_OCR_PIXELS):
    """Reject huge raster allocations *before* calling get_pixmap.

    Conservative ceil dimensions account for rotated page geometry. The cap
    is per-page, not a global memory/CPU sandbox. No silent DPI reduction.
    """
    width, height = float(page.rect.width), float(page.rect.height)
    if not all(math.isfinite(x) and x > 0 for x in (width, height)):
        raise ValueError('Géométrie de page OCR invalide')
    if type(max_pixels) is not int or max_pixels < 1:
        raise ValueError('Budget OCR invalide')
    pixels_w = math.ceil(width * dpi / 72)
    pixels_h = math.ceil(height * dpi / 72)
    if pixels_w * pixels_h > max_pixels:
        raise ValueError('Page OCR trop grande au DPI demandé : limite de pixels dépassée')
    return pixels_w, pixels_h


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
    quality: object = None  # V48.7: measured coverage, not OCR accuracy
    quality_gate: object = None  # V48.8: optional policy decision


def _digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def searchable_pdf(source, destination, language='fra+eng', dpi=200, skip_text=True, progress=None, tessdata=None, *,
                   max_ocr_pixels=DEFAULT_TOTAL_OCR_PIXELS, max_ocr_pages=DEFAULT_OCR_PAGES,
                   quality_policy=None):
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
    if skip_text not in (True, False, 'smart') or (type(skip_text) is not bool and skip_text != 'smart'):
        raise ValueError("Politique OCR invalide : True, False ou 'smart' attendus")
    if tessdata is not None and not Path(tessdata).is_dir():raise ValueError('Dossier tessdata absent')
    from openpdf_ocr_quality_gate_v488 import OCRQualityPolicy
    if quality_policy is not None and not isinstance(quality_policy, OCRQualityPolicy):
        raise TypeError('Politique de qualité OCR invalide')
    source_fingerprint = fingerprint_source(source)
    fd,tmp=tempfile.mkstemp(prefix='.openpdf-ocr-',suffix='.pdf',dir=destination.parent)
    os.close(fd)
    processed=0; skipped=0
    native_checks = {}  # 1-based page -> original native text for smart OCR
    try:
        with fitz.open(source) as original, fitz.open() as result:
            if original.needs_pass:raise ValueError('PDF chiffré non pris en charge')
            if not original.page_count:raise ValueError('PDF sans page')
            profile = preflight_ocr_document(original)
            # Preflight the *whole* job: an excessive later page must not
            # trigger expensive OCR on earlier pages before rejection.
            selected, budget = plan_ocr_pages(
                original, dpi, lambda page: should_ocr_page(page, skip_text),
                max_total_pixels=max_ocr_pixels, max_ocr_pages=max_ocr_pages)
            # V48.6: fail before rendering any page if required offline OCR
            # language packs are absent. Copy-only jobs need no Tesseract.
            if any(selected):
                from openpdf_ocr_runtime_v513 import resolve_ocr_models
                tessdata = resolve_ocr_models(language, tessdata=tessdata)
            for i,page in enumerate(original):
                if not selected[i]:
                    result.insert_pdf(original,from_page=i,to_page=i)
                    skipped+=1
                else:
                    # Rasterization of a page with native text (smart/force)
                    # must not silently destroy its extractable words.
                    native_text = page.get_text('text')
                    validate_ocr_raster(page, dpi)
                    pix=page.get_pixmap(dpi=dpi,alpha=False)
                    kwargs={'language':language}
                    if tessdata is not None:kwargs['tessdata']=str(tessdata)
                    pdf_bytes=pix.pdfocr_tobytes(**kwargs)
                    with fitz.open(stream=pdf_bytes,filetype='pdf') as recognized:
                        if native_text.strip():
                            assert_native_text_preserved(
                                native_text, recognized[0].get_text('text'), page=i+1)
                            native_checks[i+1] = native_text
                        result.insert_pdf(recognized)
                    processed+=1
                if progress:progress(i+1,original.page_count)
            if result.page_count!=original.page_count:raise RuntimeError('Nombre de pages incorrect')
            apply_ocr_document_profile(result, profile)
            result.save(tmp,garbage=3,deflate=True)
        with fitz.open(tmp) as check:
            if check.page_count!=processed+skipped:raise RuntimeError('PDF OCR invalide')
            from openpdf_ocr_quality_v487 import audit_ocr_text_coverage
            quality = audit_ocr_text_coverage(check, selected)
            gate = None
            if quality_policy is not None:
                from openpdf_ocr_quality_gate_v488 import evaluate_ocr_quality_gate
                gate = evaluate_ocr_quality_gate(quality, quality_policy)
            verify_ocr_document_profile(check, profile)
            for page_number, original_text in native_checks.items():
                assert_native_text_preserved(
                    original_text, check[page_number-1].get_text('text'),
                    page=page_number)
        if Path(tmp).stat().st_size==0:raise RuntimeError('Sortie OCR vide')
        verify_source_unchanged(source, source_fingerprint)
        # Compute the receipt before publishing: an audit failure must not leave
        # a committed document with a failed operation result.
        digest = _digest(tmp)
        size = Path(tmp).stat().st_size
        verify_source_unchanged(source, source_fingerprint)
        publish_exclusive(tmp, destination)
        return OCRReceipt(str(source),str(destination),processed+skipped,processed,skipped,digest,size,language,quality.to_dict(),gate)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
