"""Auditable compression size/quality claims, with no inferred visual score.

A report describes *performed checks*; it does not claim lossless visual
identity for JPEG profiles or certification of fidelity.
Author: Abdelhalim Talbi.
"""
from dataclasses import asdict, dataclass

LOSSLESS_PROFILES = frozenset({'standard', 'smaller_only'})
LOSSY_PROFILES = frozenset({'images_balanced', 'images_adaptive'})


@dataclass(frozen=True)
class CompressionMetrics:
    profile: str
    published: bool
    source_bytes: int
    output_bytes: int
    saved_bytes: int
    saving_percent: float
    output_to_source_percent: float
    source_sha256: str
    quality_evidence: str

    def to_dict(self):
        return asdict(self)


def build_metrics(*, profile, source_bytes, output_bytes, source_sha256,
                  published, canonical_engine):
    if profile not in LOSSLESS_PROFILES | LOSSY_PROFILES:
        raise ValueError('Profil de compression inconnu')
    if type(source_bytes) is not int or source_bytes <= 0:
        raise ValueError('Taille de source invalide')
    if type(output_bytes) is not int or output_bytes < 0:
        raise ValueError('Taille de sortie invalide')
    if type(published) is not bool or type(canonical_engine) is not bool:
        raise TypeError('Statut de compression invalide')
    if published != (output_bytes > 0):
        raise ValueError('Statut de publication incompatible avec la taille')
    if not isinstance(source_sha256, str) or len(source_sha256) != 64 or any(
            c not in '0123456789abcdef' for c in source_sha256):
        raise ValueError('Empreinte source SHA-256 invalide')
    evidence = ('not_applicable_no_output' if not published else
                'unverified_injected_engine' if not canonical_engine else
                'lossless_image_and_render_checks' if profile in LOSSLESS_PROFILES else
                'sampled_lossy_render_checks')
    saved = source_bytes - output_bytes if published else 0
    return CompressionMetrics(
        profile, published, source_bytes, output_bytes, saved,
        round(100 * saved / source_bytes, 2),
        round(100 * output_bytes / source_bytes, 2) if published else 0.0,
        source_sha256, evidence)
