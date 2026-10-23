"""Native PDF page rotation, preserving text and source file."""
from pathlib import Path
import os
import tempfile
import fitz
from openpdf_atomic_output import publish_exclusive

def rotate_pdf(source, destination, angle=90):
    src=Path(source).expanduser().resolve(strict=True)
    dst=Path(destination).expanduser().resolve()
    angle=int(angle)
    if angle not in (90,180,270):
        raise ValueError('Rotation : 90, 180 ou 270 degrés attendus')
    if not src.is_file() or src.suffix.lower()!='.pdf' or dst.suffix.lower()!='.pdf':
        raise ValueError('Source et destination PDF obligatoires')
    if src==dst:
        raise ValueError('Source et destination identiques')
    if not dst.parent.is_dir():
        raise ValueError('Dossier de destination absent')
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(f'Destination existante : {dst}')
    before=src.stat()
    identity=(before.st_size,before.st_mtime_ns,before.st_ino)
    fd,name=tempfile.mkstemp(prefix='.openpdf-rotate-',suffix='.pdf',dir=dst.parent)
    os.close(fd)
    tmp=Path(name)
    try:
        with fitz.open(src) as pdf:
            if pdf.needs_pass:
                raise ValueError('PDF protégé')
            if pdf.page_count==0:
                raise ValueError('PDF sans page')
            for page in pdf:
                page.set_rotation((page.rotation+angle)%360)
            pdf.save(tmp,garbage=3,deflate=True)
        with fitz.open(tmp) as check:
            if check.page_count==0:
                raise RuntimeError('Rotation invalide')
        after=src.stat()
        if (after.st_size,after.st_mtime_ns,after.st_ino)!=identity:
            raise RuntimeError('Source modifiée pendant la rotation')
        publish_exclusive(tmp,dst)
        return dst
    finally:
        tmp.unlink(missing_ok=True)
