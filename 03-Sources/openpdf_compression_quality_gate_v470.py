"""Validated compression quality limits. Author: Abdelhalim Talbi."""
from dataclasses import dataclass
import math
from openpdf_source_integrity_v430 import fingerprint_source
from openpdf_compression_visual_audit_v469 import CompressionVisualAudit

@dataclass(frozen=True)
class CompressionQualityGate:
    max_page_mae: float = 4.0
    max_page_changed_fraction: float = .02
    render_scale: float = .5
    sample_step: int = 4
    pixel_delta: int = 24

def validate_quality_gate(g):
    if type(g) is not CompressionQualityGate:
        raise ValueError('Invalid compression policy')
    for x, low, high in ((g.max_page_mae,0,255),(g.max_page_changed_fraction,0,1),(g.render_scale,.25,2)):
        if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not low <= x <= high:
            raise ValueError('Invalid quality threshold')
    if type(g.sample_step) is not int or not 1 <= g.sample_step <= 32 or type(g.pixel_delta) is not int or not 0 <= g.pixel_delta <= 255:
        raise ValueError('Invalid sampling policy')
    return g

def enforce_quality_gate(a, src, dst, g):
    validate_quality_gate(g)
    if type(a) is not CompressionVisualAudit or a.pages_compared < 1 or a.pixels_sampled < a.pages_compared:
        raise RuntimeError('Missing quality evidence')
    if a.sample_step > g.sample_step or a.render_scale < g.render_scale or a.pixel_delta > g.pixel_delta:
        raise RuntimeError('Audit precision below policy')
    if not a.text_identical or not a.geometry_identical:
        raise RuntimeError('PDF content changed')
    if fingerprint_source(src).sha256 != a.source_sha256 or fingerprint_source(dst).sha256 != a.candidate_sha256:
        raise RuntimeError('PDF hash changed')
    if a.max_page_mae > g.max_page_mae or a.max_page_changed_fraction > g.max_page_changed_fraction:
        raise RuntimeError('Visual degradation exceeds policy')
    return a
