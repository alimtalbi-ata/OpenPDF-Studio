"""UI-independent, transactional text conversion controller. Abdelhalim Talbi.

Conversions extract editable text, not original PDF layout or native tables.
"""
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile
from openpdf_core_v260 import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, extract_text
from openpdf_output_policy_v300 import validate_output, OutputConflictError

CONVERTERS = {'docx': pdf_to_docx, 'xlsx': pdf_to_xlsx, 'pptx': pdf_to_pptx, 'txt': extract_text}

@dataclass(frozen=True)
class ConversionResult:
    format: str
    destination: Path
    bytes_written: int

class ConversionController:
    def convert(self, source, destination, format=None):
        src = Path(source).expanduser().resolve(strict=True)
        dest = Path(destination).expanduser().resolve()
        ext = (format or dest.suffix.lstrip('.')).lower().lstrip('.')
        if ext not in CONVERTERS or dest.suffix.lower() != '.' + ext:
            raise ValueError('Format de sortie invalide : docx, xlsx, pptx ou txt')
        if not src.is_file() or src.suffix.lower() != '.pdf':
            raise ValueError('Source PDF invalide')
        if not dest.parent.is_dir():
            raise ValueError('Dossier de destination introuvable')
        validate_output([src], dest)
        # Never write directly into the destination: a conversion failure must
        # preserve any existing user file. os.replace commits only on success.
        fd, tmp_name = tempfile.mkstemp(prefix='.openpdf-convert-', suffix='.'+ext, dir=dest.parent)
        os.close(fd)
        temp = Path(tmp_name)
        try:
            CONVERTERS[ext](src, temp)
            if not temp.is_file() or temp.stat().st_size == 0:
                raise RuntimeError('Conversion vide')
            size = temp.stat().st_size
            os.replace(temp, dest)
            return ConversionResult(ext, dest, size)
        finally:
            temp.unlink(missing_ok=True)
