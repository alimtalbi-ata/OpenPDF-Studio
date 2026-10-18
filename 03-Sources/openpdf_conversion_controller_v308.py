"""V30.8: conversion atomique avec annulation coopérative avant publication."""
from pathlib import Path
import os, tempfile
from openpdf_conversion_controller_v301 import ConversionResult, CONVERTERS
from openpdf_output_policy_v300 import validate_output

class ConversionCancelled(RuntimeError):
    pass

class ConversionController:
    def convert(self, source, destination, format=None, *, cancelled=None, progress=None):
        def check():
            if cancelled is not None and cancelled():
                raise ConversionCancelled('Conversion annulée : destination préservée')
        check()
        src = Path(source).expanduser()
        if not src.is_file() or src.suffix.lower() != '.pdf':
            raise ValueError('Sélectionnez un fichier PDF source existant')
        src = src.resolve(strict=True)
        dest = Path(destination).expanduser().resolve()
        ext = (format or dest.suffix.lstrip('.')).lower().lstrip('.')
        if ext not in CONVERTERS or dest.suffix.lower() != '.' + ext:
            raise ValueError('Format de sortie invalide : docx, xlsx, pptx ou txt')
        if not dest.parent.is_dir():
            raise ValueError('Dossier de destination introuvable')
        validate_output([src], dest)
        check()
        fd, tmp_name = tempfile.mkstemp(prefix='.openpdf-convert-', suffix='.'+ext, dir=dest.parent)
        os.close(fd)
        temp = Path(tmp_name)
        try:
            CONVERTERS[ext](src, temp)
            check()  # Never commit a cancelled conversion.
            if not temp.is_file() or temp.stat().st_size == 0:
                raise RuntimeError('La conversion a produit un fichier vide')
            size = temp.stat().st_size
            os.replace(temp, dest)
            if progress is not None: progress(1, 1)
            return ConversionResult(ext, dest, size)
        finally:
            temp.unlink(missing_ok=True)
