"""Offline OCR language-data preflight for the PyMuPDF/Tesseract engine.

Checks the actual tessdata directory consumed by PyMuPDF (not the optional
`tesseract` CLI). Never downloads language packs or executes external commands.
A file's presence is not proof of valid model contents or OCR accuracy.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from pathlib import Path
import re

LANGUAGE_PATTERN = re.compile(r'[A-Za-z]{3}(?:\+[A-Za-z]{3})*\Z')
MAX_TRAINEDDATA_BYTES = 512 * 1024 * 1024
MIN_TRAINEDDATA_BYTES = 1024


def preflight_ocr_languages(language: str, tessdata=None, *, get_tessdata=None):
    """Fail before rasterization if any requested OCR language is unavailable.

    Returns a serializable readiness receipt without exposing model file paths
    to the application's regular success message. The caller must still pass
    the same `tessdata` argument to pix.pdfocr_tobytes.
    """
    if not isinstance(language, str) or not LANGUAGE_PATTERN.fullmatch(language):
        raise ValueError('Langue OCR invalide')
    if get_tessdata is None:
        import fitz
        get_tessdata = fitz.get_tessdata
    if tessdata is None:
        folder = get_tessdata()
    else:
        folder = tessdata
    if folder is None or not isinstance(folder, (str, Path)):
        raise RuntimeError('Dossier tessdata introuvable : OCR indisponible')
    directory = Path(folder).expanduser()
    if not directory.is_dir():
        raise RuntimeError('Dossier tessdata introuvable : OCR indisponible')
    languages = tuple(dict.fromkeys(language.lower().split('+')))
    missing = []
    invalid = []
    for code in languages:
        file = directory / f'{code}.traineddata'
        try:
            if not file.is_file():
                missing.append(code)
                continue
            size = file.stat().st_size
        except OSError:
            missing.append(code)
            continue
        if not MIN_TRAINEDDATA_BYTES <= size <= MAX_TRAINEDDATA_BYTES:
            invalid.append(code)
    if missing:
        raise RuntimeError('Langue(s) OCR absente(s) de tessdata : ' + ', '.join(missing))
    if invalid:
        raise RuntimeError('Modèle(s) OCR de taille invalide : ' + ', '.join(invalid))
    return {'languages': languages, 'model_files_checked': len(languages),
            'check': 'traineddata_presence_and_size_only',
            'ocr_accuracy_certified': False}
