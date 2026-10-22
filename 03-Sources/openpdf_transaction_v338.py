"""V33.8: explicit publication receipt emitted in the worker, not inferred by GUI."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
from openpdf_compression_v327 import compress_with_profile

@dataclass(frozen=True)
class CompressionReceipt:
    published: bool
    destination: str
    message: str
    size: int = 0
    sha256: str = ''
    metrics: object = None  # V46.8: optional structured, auditable size/quality report

def compress_with_receipt(source, destination, profile='smaller_only'):
    """Preserve legacy engine semantics, return authoritative publish status.

    A no-gain result is *never* published, even if an older destination exists.
    """
    message = str(compress_with_profile(source, destination, profile))
    if message.startswith('Aucun gain') or 'Aucun fichier de sortie modifié' in message:
        return CompressionReceipt(False, str(destination), message)
    path = Path(destination)
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError('Le moteur indique une sortie, mais le fichier est absent ou vide')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return CompressionReceipt(True, str(path.resolve()), message, path.stat().st_size, digest.hexdigest())

def verify_receipt(receipt, destination):
    if not isinstance(receipt, CompressionReceipt):
        return False, 'Aucun reçu transactionnel émis par le moteur.'
    if not receipt.published:
        return False, receipt.message
    path = Path(destination)
    if path.resolve() != Path(receipt.destination).resolve():
        return False, 'Destination différente du reçu.'
    if not path.is_file() or path.stat().st_size != receipt.size:
        return False, 'Fichier absent ou taille différente du reçu.'
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    if digest.hexdigest() != receipt.sha256:
        return False, 'Contenu modifié depuis la publication.'
    return True, 'Publication confirmée par SHA-256.'
