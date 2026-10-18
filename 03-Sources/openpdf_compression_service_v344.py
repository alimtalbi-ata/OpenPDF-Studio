"""Compression service with explicit, testable publication semantics.

Author: Abdelhalim Talbi. No Tkinter dependency.
"""
from dataclasses import dataclass
from pathlib import Path
from openpdf_compression_v327 import PROFILES, compress_with_profile
from openpdf_transaction_v338 import CompressionReceipt, verify_receipt

@dataclass(frozen=True)
class CompressionRequest:
    source: str
    destination: str
    profile: str = "smaller_only"


def validate_compression_request(request):
    if request.profile not in PROFILES:
        raise ValueError("Profil de compression inconnu")
    src = Path(request.source).expanduser().resolve()
    dst = Path(request.destination).expanduser().resolve()
    if not src.is_file() or src.suffix.lower() != ".pdf":
        raise ValueError("PDF source inexistant ou invalide")
    if src == dst:
        raise ValueError("Source et destination identiques")
    if not dst.parent.is_dir():
        raise ValueError("Dossier de destination inexistant")
    return src, dst


def execute_compression(request, engine=compress_with_profile):
    src, dst = validate_compression_request(request)
    # A no-gain result must never be interpreted as a new publication.
    # The legacy engine writes atomically via os.replace on success.
    from openpdf_transaction_v338 import compress_with_receipt as legacy_receipt
    if engine is compress_with_profile:
        receipt = legacy_receipt(str(src), str(dst), request.profile)
    else:
        # Dependency injection supports deterministic contract testing.
        message = str(engine(str(src), str(dst), request.profile))
        if message.startswith("Aucun gain") or "Aucun fichier de sortie modifié" in message:
            return CompressionReceipt(False, str(dst), message)
        from hashlib import sha256
        if not dst.is_file() or dst.stat().st_size == 0:
            raise RuntimeError("Aucune sortie valide publiée")
        digest = sha256()
        with dst.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024), b""):
                digest.update(block)
        receipt = CompressionReceipt(True, str(dst), message, dst.stat().st_size, digest.hexdigest())
    if receipt.published:
        valid, reason = verify_receipt(receipt, dst)
        if not valid:
            raise RuntimeError("Publication non vérifiable : " + reason)
    return receipt


def compress_with_receipt(source, destination, profile="smaller_only"):
    """GUI-compatible worker; returns existing typed CompressionReceipt."""
    return execute_compression(CompressionRequest(source, destination, profile))
