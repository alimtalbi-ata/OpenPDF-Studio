"""Opt-in, fail-closed compression quality gate for sampled PDF render audits.

The gate is applied to a private candidate *before* exclusive publication.
Sampling cannot certify visual, archival, semantic or accessibility fidelity.
Author: Abdelhalim Talbi.
"""
from dataclasses import dataclass
import math
from pathlib import Path

from openpdf_source_integrity_v430 import fingerprint_source
from openpdf_compression_visual_audit_v469 import CompressionVisualAudit


@dataclass(frozen=True)
class CompressionQualityGate:
    """User-selected upper bounds for measured RGB degradation.

    MAE is a per-channel error on 0..255. Changed fraction is in 0..1.
    Every page is rendered but pixels are sampled on a regular grid.
    """
    max_page_mae: float = 4.0
    max_page_changed_fraction: float = 0.02
    render_scale: float = 0.5
    sample_step: int = 4
    pixel_delta: int = 24  # RGB-channel tolerance used for changed-pixel fraction


def validate_quality_gate(gate):
    if type(gate) is not CompressionQualityGate:
        raise ValueError('Politique de qualité de compression invalide')
    for name, lower, upper in (
        ('max_page_mae', 0.0, 255.0),
        ('max_page_changed_fraction', 0.0, 1.0),
        ('render_scale', 0.25, 2.0),
    ):
        value = getattr(gate, name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f'Limite de qualité invalide : {name}')
    if type(gate.sample_step) is not int or not 1 <= gate.sample_step <= 32:
        raise ValueError('Pas d’échantillonnage invalide')
    if type(gate.pixel_delta) is not int or not 0 <= gate.pixel_delta <= 255:
        raise ValueError('Tolérance de différence par pixel invalide')
    return gate


def enforce_quality_gate(audit, source, candidate, gate):
    """Reject unverified/modified inputs or a candidate exceeding thresholds.

    Raises RuntimeError before publication. Does not modify any file.
    """
    validate_quality_gate(gate)
    if type(audit) is not CompressionVisualAudit:
        raise RuntimeError('Audit visuel absent ou invalide : publication refusée')
    if type(audit.pages_compared) is not int or audit.pages_compared < 1 or type(audit.pixels_sampled) is not int or audit.pixels_sampled < audit.pages_compared:
        raise RuntimeError('Audit visuel incomplet : publication refusée')
    # A claimed measurement must meet (or exceed) the requested precision.
    # Otherwise a report with sample_step=32 or pixel_delta=255 could
    # silently satisfy a supposedly strict quality gate.
    if (audit.evidence != 'bounded_sampled_rgb_render_not_fidelity_certification'
            or type(audit.sample_step) is not int or audit.sample_step < 1
            or audit.sample_step > gate.sample_step
            or isinstance(audit.render_scale, bool)
            or not isinstance(audit.render_scale, (int, float))
            or not math.isfinite(audit.render_scale)
            or audit.render_scale < gate.render_scale
            or type(audit.pixel_delta) is not int or audit.pixel_delta < 0
            or audit.pixel_delta > gate.pixel_delta):
        raise RuntimeError('Précision de l’audit inférieure à la politique : publication refusée')
    if audit.text_identical is not True or audit.geometry_identical is not True:
        raise RuntimeError('Texte ou géométrie modifié : publication refusée')
    for name, upper in (('max_page_mae', 255.0), ('max_page_changed_fraction', 1.0)):
        value = getattr(audit, name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= upper:
            raise RuntimeError('Mesure visuelle non fiable : publication refusée')
    # V47.5: hashes and low MAE cannot substitute for auditing every page.
    from openpdf_audit_coverage_v475 import verify_audit_coverage
    verify_audit_coverage(audit, source, candidate)
    # Check both byte identities again, not only the earlier audit's claims.
    if fingerprint_source(Path(source)).sha256 != audit.source_sha256:
        raise RuntimeError('Empreinte source divergente : publication refusée')
    if fingerprint_source(Path(candidate)).sha256 != audit.candidate_sha256:
        raise RuntimeError('Empreinte candidate divergente : publication refusée')
    if audit.max_page_mae > gate.max_page_mae:
        raise RuntimeError('Dégradation visuelle MAE supérieure au seuil : publication refusée')
    if audit.max_page_changed_fraction > gate.max_page_changed_fraction:
        raise RuntimeError('Fraction de pixels modifiés supérieure au seuil : publication refusée')
    return audit
