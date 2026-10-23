"""Bounded, fail-closed adaptive JPEG compression for OpenPDF Studio V44.4.

Author: Abdelhalim Talbi.

A candidate that is not smaller than its source is never rendered for quality
checks. Recoverable errors in one JPEG trial do not prevent a later quality
from succeeding; source-integrity failures are always fatal.
"""
from pathlib import Path
import os
import tempfile

QUALITIES = (55, 70, 85)
RECOVERABLE_TRIAL_ERRORS = (OSError, RuntimeError, ValueError)


def select_adaptive_candidate(source, destination_temp, *, compressor,
                              source_fingerprint, qualities=QUALITIES):
    """Select smallest fully verified candidate; never publish a failed trial.

    Returns ``(quality, bytes, attempts)`` or ``(None, None, attempts)`` if
    candidates were non-beneficial. If all candidates failed compression or
    validation, raises RuntimeError. Every attempt has a documented status:
    ``accepted``, ``no_gain``, or ``rejected``. A modified source is fatal.
    """
    from openpdf_source_integrity_v430 import verify_source_unchanged
    from openpdf_quality_v327 import assess_candidate
    from openpdf_lossy_quality_v436 import validate_lossy_render
    from openpdf_structure_guard_v439 import validate_structure_preserved

    source = Path(source)
    destination_temp = Path(destination_temp)
    if source.resolve() == destination_temp.resolve():
        raise ValueError('Source et candidat identiques')
    if (not isinstance(qualities, tuple) or not qualities
            or len(qualities) > 3 or len(set(qualities)) != len(qualities)
            or any(type(q) is not int or not 30 <= q <= 95 for q in qualities)):
        raise ValueError('Liste de qualités invalide (1 à 3 valeurs de 30 à 95)')

    attempts = []
    best_size = None
    best_quality = None
    best_path = None
    try:
        for quality in qualities:
            verify_source_unchanged(source, source_fingerprint)
            fd, name = tempfile.mkstemp(prefix='.openpdf-adaptive-', suffix='.pdf',
                                        dir=str(destination_temp.parent))
            os.close(fd)
            trial = Path(name)
            try:
                # Verify in finally even when the compressor raises: source
                # mutations must never be swallowed as a recoverable trial.
                compressor_error = None
                try:
                    try:
                        compressor(source, trial, dpi_target=150, quality=quality)
                    except RECOVERABLE_TRIAL_ERRORS as exc:
                        compressor_error = exc
                finally:
                    # Outside the recoverable exception handler: never mask
                    # a modified source with a failed JPEG trial.
                    verify_source_unchanged(source, source_fingerprint)
                if compressor_error is not None:
                    attempts.append({'quality': quality, 'status': 'rejected',
                                     'reason': f'Compression impossible : {compressor_error}'[:240]})
                    continue

                try:
                    size = trial.stat().st_size
                except OSError as exc:
                    attempts.append({'quality': quality, 'status': 'rejected',
                                     'reason': f'Candidat indisponible : {exc}'[:240]})
                    continue
                if not size:
                    attempts.append({'quality': quality, 'status': 'rejected',
                                     'reason': 'Candidat PDF vide'})
                    continue
                if size >= source_fingerprint.size:
                    # No chance of publication; avoid three costly full-page
                    # render/structure passes for large or uncompressible PDFs.
                    attempts.append({'quality': quality, 'status': 'no_gain',
                                     'bytes': size})
                    continue

                try:
                    text = assess_candidate(source, trial)
                    if text['pages_texte_modifie']:
                        raise RuntimeError('Texte extrait modifié')
                    visual = validate_lossy_render(source, trial)
                    structure = validate_structure_preserved(source, trial)
                except RECOVERABLE_TRIAL_ERRORS as exc:
                    attempts.append({'quality': quality, 'status': 'rejected',
                                     'reason': str(exc)[:240]})
                    continue
                finally:
                    verify_source_unchanged(source, source_fingerprint)

                attempts.append({'quality': quality, 'status': 'accepted',
                                 'bytes': size, 'max_mae': visual['max_mae'],
                                 'max_tile_mae': visual['max_tile_mae'],
                                 'pages': structure['pages_verified']})
                if best_size is None or size < best_size:
                    if best_path is not None:
                        best_path.unlink()
                    best_size, best_quality, best_path = size, quality, trial
                    trial = None
            finally:
                if trial is not None:
                    trial.unlink(missing_ok=True)

        verify_source_unchanged(source, source_fingerprint)
        if best_path is None:
            if any(a['status'] == 'no_gain' for a in attempts):
                return None, None, attempts
            raise RuntimeError('Aucun candidat adaptatif conforme aux contrôles : '
                               + '; '.join(f"Q{a['quality']}: {a['reason']}"
                                           for a in attempts))
        os.replace(best_path, destination_temp)
        best_path = None
        return best_quality, best_size, attempts
    finally:
        if best_path is not None:
            best_path.unlink(missing_ok=True)
