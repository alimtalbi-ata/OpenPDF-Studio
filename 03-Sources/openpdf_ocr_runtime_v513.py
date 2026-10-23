"""V51.3: deterministic, offline OCR model resolution for Windows binaries.

Bundled eng/fra models are pinned to official tessdata_fast Git blobs and SHA256.
No runtime downloads, implicit model fallback, or OCR accuracy claims.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile

# Official tesseract-ocr/tessdata_fast Git tree; independently checked against
# local Debian models with matching Git blob IDs.
BUNDLED_MODELS = {
    'eng': ('7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2', 4113088),
    'fra': ('ced037562e8c80c13122dece28dd477d399af80911a28791a66a63ac1e3445ca', 1130365),
}


def _check_directory(directory: Path, language: str, *, pinned: bool) -> Path:
    from openpdf_ocr_language_preflight_v486 import preflight_ocr_languages
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError('Dossier OCR absent ou lien symbolique interdit')
    for code in dict.fromkeys(language.lower().split('+')):
        model = directory / (code + '.traineddata')
        if model.is_symlink():
            raise RuntimeError('Modele OCR symbolique interdit : ' + code)
        if pinned:
            if code not in BUNDLED_MODELS:
                raise RuntimeError('Langue OCR non incluse dans le portable : ' + code)
            expected_hash, expected_size = BUNDLED_MODELS[code]
            if not model.is_file() or model.stat().st_size != expected_size:
                raise RuntimeError('Modele OCR integre absent ou de taille invalide : ' + code)
            with model.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != expected_hash:
                raise RuntimeError('Modele OCR integre altere : ' + code)
    preflight_ocr_languages(language, tessdata=directory)
    return directory


def resolve_ocr_models(language='fra+eng', *, tessdata=None, executable=None,
                       bundle_root=None, frozen=None, system_tessdata=None):
    """Resolve exactly the models used by PyMuPDF, rejecting damaged bundles.

    Priority: explicit tessdata, OPENPDF_TESSDATA_DIR, frozen bundle, system.
    A frozen binary never silently falls back to system-installed models.
    """
    from openpdf_ocr_language_preflight_v486 import LANGUAGE_PATTERN
    if not isinstance(language, str) or not LANGUAGE_PATTERN.fullmatch(language):
        raise ValueError('Langue OCR invalide')
    if tessdata is not None:
        return _check_directory(Path(tessdata).expanduser(), language, pinned=False)
    env_dir = os.environ.get('OPENPDF_TESSDATA_DIR')
    if env_dir is not None:
        if not env_dir.strip():
            raise RuntimeError('OPENPDF_TESSDATA_DIR vide')
        return _check_directory(Path(env_dir).expanduser(), language, pinned=False)
    is_frozen = bool(getattr(sys, 'frozen', False)) if frozen is None else bool(frozen)
    if is_frozen:
        roots = []
        if bundle_root is not None:
            roots.append(Path(bundle_root))
        elif getattr(sys, '_MEIPASS', None):
            roots.append(Path(sys._MEIPASS))
        exe = Path(executable) if executable is not None else Path(sys.executable)
        roots.append(exe.parent)
        for root in roots:
            candidate = root / 'tessdata'
            if candidate.exists() or candidate.is_symlink():
                return _check_directory(candidate, language, pinned=True)
        raise RuntimeError('Modeles OCR integres absents : eng/fra requis dans le portable')
    if system_tessdata is None:
        import fitz
        system_tessdata = fitz.get_tessdata()
    if not system_tessdata:
        raise RuntimeError('Modele OCR systeme indisponible')
    return _check_directory(Path(system_tessdata), language, pinned=False)


def functional_ocr_self_test():
    """Run actual embedded Tesseract OCR on a raster-only PDF, no GUI needed."""
    import fitz
    from openpdf_ocr_service_v347 import searchable_pdf
    models = resolve_ocr_models('fra+eng')
    with tempfile.TemporaryDirectory(prefix='openpdf-ocr-selftest-') as folder:
        source = Path(folder) / 'scan.pdf'
        output = Path(folder) / 'recognized.pdf'
        with fitz.open() as text_doc:
            page = text_doc.new_page(width=600, height=240)
            page.insert_text((35, 115), 'OPENPDF OCR CHECK 12345', fontsize=32)
            png = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes('png')
        with fitz.open() as scanned:
            page = scanned.new_page(width=600, height=240)
            page.insert_image(page.rect, stream=png)
            scanned.save(source)
        receipt = searchable_pdf(source, output, language='fra+eng', tessdata=models)
        with fitz.open(output) as verified:
            extracted = verified[0].get_text('text').upper()
        if receipt.ocr_pages != 1 or 'OPENPDF' not in extracted or '12345' not in extracted:
            raise RuntimeError('OCR reel non conforme : texte attendu non reconnu')
        if hashlib.sha256(output.read_bytes()).hexdigest() != receipt.sha256:
            raise RuntimeError('Empreinte OCR non conforme')
        return {'schema': 'openpdf.ocr-runtime.v51.3', 'passed': True,
                'ocr_pages': receipt.ocr_pages, 'languages': ['fra', 'eng'],
                'output_sha256_verified': True,
                'accuracy_certified': False, 'windows_gui_qualified': False}
