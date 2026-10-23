"""Compression service with explicit, testable publication semantics.

Author: Abdelhalim Talbi. No Tkinter dependency.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from openpdf_compression_v327 import PROFILES, compress_with_profile
from openpdf_transaction_v338 import CompressionReceipt, verify_receipt
from openpdf_compression_metrics_v468 import build_metrics
from openpdf_source_integrity_v430 import fingerprint_source, verify_source_unchanged

@dataclass(frozen=True)
class CompressionRequest:
    source: str
    destination: str
    profile: str = "smaller_only"
    measure_visual: bool = False  # V46.9 opt-in; extra rendering cost
    quality_gate: object = None  # V47.0 opt-in fail-closed quality thresholds
    full_pixel_gate: object = None  # V48.9 bounded full-RGB-pixel acceptance


def validate_compression_request(request):
    if type(request.measure_visual) is not bool:
        raise ValueError('Option de mesure visuelle invalide')
    if request.quality_gate is not None:
        from openpdf_compression_quality_gate_v470 import validate_quality_gate
        validate_quality_gate(request.quality_gate)
    if request.full_pixel_gate is not None:
        from openpdf_compression_acceptance_v489 import AcceptancePolicy
        if type(request.full_pixel_gate) is not AcceptancePolicy:
            raise ValueError('Politique RGB V48.9 invalide')
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
    source_fingerprint = fingerprint_source(src)
    canonical_engine = engine is compress_with_profile
    # A no-gain result must never be interpreted as a new publication.
    # The legacy engine writes atomically via os.replace on success.
    from openpdf_transaction_v338 import compress_with_receipt as legacy_receipt
    if (request.measure_visual or request.quality_gate is not None or request.full_pixel_gate is not None) and not canonical_engine:
        raise ValueError('Mesure visuelle impossible avec moteur injecté')
    if engine is compress_with_profile:
        if request.measure_visual or request.quality_gate is not None or request.full_pixel_gate is not None:
            from openpdf_compression_visual_audit_v469 import audit_compression_pair
            def checked_audit(source, candidate):
                sampled = None
                if request.measure_visual or request.quality_gate is not None:
                    if request.quality_gate is None:
                        sampled = audit_compression_pair(source, candidate)
                    else:
                        from openpdf_compression_quality_gate_v470 import enforce_quality_gate
                        gate = request.quality_gate
                        report = audit_compression_pair(source, candidate,
                                                        scale=gate.render_scale,
                                                        sample_step=gate.sample_step,
                                                        pixel_delta=gate.pixel_delta)
                        sampled = enforce_quality_gate(report, source, candidate, gate)
                full = None
                if request.full_pixel_gate is not None:
                    from openpdf_compression_acceptance_v489 import audit_compression_candidate
                    full = audit_compression_candidate(source, candidate, request.full_pixel_gate)
                if sampled is not None and full is not None:
                    return {'sampled_visual_audit': sampled.to_dict(), 'full_pixel_acceptance': full}
                return full if full is not None else sampled
            receipt = legacy_receipt(str(src), str(dst), request.profile,
                                     audit_collector=checked_audit)
        else:
            receipt = legacy_receipt(str(src), str(dst), request.profile)
    else:
        # Dependency injection supports deterministic contract testing.
        message = str(engine(str(src), str(dst), request.profile))
        if message.startswith("Aucun gain") or "Aucun fichier de sortie modifié" in message:
            receipt = CompressionReceipt(False, str(dst), message)
        else:
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
    verify_source_unchanged(src, source_fingerprint)
    metrics = build_metrics(profile=request.profile, source_bytes=source_fingerprint.size,
                            output_bytes=receipt.size if receipt.published else 0,
                            source_sha256=source_fingerprint.sha256,
                            published=receipt.published, canonical_engine=canonical_engine,
                            visual_audit=receipt.visual_audit)
    return replace(receipt, metrics=metrics)


def compress_with_receipt(source, destination, profile="smaller_only"):
    """GUI-compatible worker; returns existing typed CompressionReceipt."""
    return execute_compression(CompressionRequest(source, destination, profile))
