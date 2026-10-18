"""Office conversion service: atomic output + structural audit. Abdelhalim Talbi."""
from pathlib import Path
import hashlib
from dataclasses import dataclass
from openpdf_conversion_controller_v309 import ConversionController
from openpdf_conversion_audit_v346 import audit_conversion
from openpdf_atomic_output import publish_exclusive

SUPPORTED_FORMATS = ('docx', 'xlsx', 'pptx')

@dataclass(frozen=True)
class ConversionOutcome:
    destination: str
    output_format: str
    bytes_written: int
    sha256: str
    warnings: tuple

def convert_office(source, destination, *, output_format=None):
    source, destination = Path(source), Path(destination)
    fmt = (output_format or destination.suffix.lstrip('.')).lower()
    if fmt not in SUPPORTED_FORMATS or destination.suffix.lower() != '.' + fmt:
        raise ValueError('Format Office invalide : docx, xlsx ou pptx')
    # Validate the source and target before the historical transactional converter runs.
    if not source.is_file() or source.suffix.lower() != '.pdf':
        raise ValueError('Source PDF invalide')
    if source.resolve() == destination.resolve():
        raise ValueError('Source et destination identiques')
    if not destination.parent.is_dir():
        raise ValueError('Dossier de destination absent')
    import os, tempfile
    from openpdf_conversion_controller_v301 import CONVERTERS
    from openpdf_output_policy_v300 import validate_output
    validate_output([source.resolve()], destination.resolve())
    if destination.exists():
        raise FileExistsError(f'Destination existante : {destination}')
    fd, tmp_name = tempfile.mkstemp(prefix='.openpdf-office-', suffix='.' + fmt, dir=destination.parent)
    os.close(fd)
    temporary = Path(tmp_name)
    try:
        CONVERTERS[fmt](source, temporary)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError('Conversion vide')
        # Audit BEFORE publication: preserve an existing destination on failure.
        audit = audit_conversion(source, temporary)
        size = temporary.stat().st_size
        # Verify the actual bytes rather than trusting a converter/audit report.
        with temporary.open('rb') as digest_stream:
            actual_sha256 = hashlib.file_digest(digest_stream, 'sha256').hexdigest()
        if audit.sha256.lower() != actual_sha256:
            raise RuntimeError('Empreinte de conversion incoherente : sortie non publiee')
        publish_exclusive(temporary, destination)
        return ConversionOutcome(str(destination), fmt, size, actual_sha256, audit.warnings)
    finally:
        temporary.unlink(missing_ok=True)
