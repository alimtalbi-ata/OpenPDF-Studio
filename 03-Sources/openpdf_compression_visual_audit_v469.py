"""Bounded, quantitative PDF compression render comparison before publication.

This is a sampled RGB comparison, not a certification of visual, semantic,
accessibility or archival fidelity. It never modifies its inputs.
Author: Abdelhalim Talbi.
"""
from dataclasses import dataclass, asdict
import math
from pathlib import Path

import fitz
from openpdf_source_integrity_v430 import fingerprint_source, verify_source_unchanged


@dataclass(frozen=True)
class CompressionVisualAudit:
    pages_compared: int
    pixels_sampled: int
    max_page_mae: float
    max_page_changed_fraction: float
    text_identical: bool
    geometry_identical: bool
    source_sha256: str
    candidate_sha256: str
    render_scale: float
    sample_step: int
    pixel_delta: int
    evidence: str = 'bounded_sampled_rgb_render_not_fidelity_certification'

    def to_dict(self):
        return asdict(self)


def _geometry(page):
    return (tuple(round(float(x), 4) for x in page.mediabox),
            tuple(round(float(x), 4) for x in page.cropbox), int(page.rotation))


def _pixmap(page, scale, max_pixels):
    box = page.rect
    if box.is_empty or box.is_infinite or box.width <= 0 or box.height <= 0:
        raise ValueError('Géométrie PDF invalide pour audit')
    # The +2 margin covers renderer rounding before any allocation.
    if (box.width * scale + 2) * (box.height * scale + 2) > max_pixels:
        raise ValueError('Budget de pixels par page dépassé avant rendu')
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                          colorspace=fitz.csRGB, alpha=False, annots=True)
    if pix.width * pix.height > max_pixels or pix.n != 3:
        raise ValueError('Rendu PDF hors budget ou format inattendu')
    return pix


def audit_compression_pair(source, candidate, *, scale=0.5, sample_step=4,
                           max_pixels_per_page=12_000_000,
                           max_total_pixels=100_000_000, max_pages=500,
                           pixel_delta=24):
    """Return measured RGB error for every page; reject unsafe/incomplete audits.

    MAE is the mean absolute error of sampled RGB channels (0..255).
    Changed fraction is the fraction of sampled pixels with any channel delta
    sum > 3 * pixel_delta. Neither metric establishes document fidelity.
    """
    if (isinstance(scale, bool) or not isinstance(scale, (int, float))
            or not math.isfinite(scale) or not 0.25 <= scale <= 2
            or type(sample_step) is not int or not 1 <= sample_step <= 32
            or type(max_pixels_per_page) is not int or not 10_000 <= max_pixels_per_page <= 12_000_000
            or type(max_total_pixels) is not int or not 10_000 <= max_total_pixels <= 500_000_000
            or type(max_pages) is not int or not 1 <= max_pages <= 10_000
            or type(pixel_delta) is not int or not 0 <= pixel_delta <= 255):
        raise ValueError('Paramètres de mesure visuelle invalides')
    src, dst = Path(source).resolve(), Path(candidate).resolve()
    if src == dst or not src.is_file() or not dst.is_file():
        raise ValueError('Deux PDF distincts et existants sont requis')
    source_before = fingerprint_source(src)
    candidate_before = fingerprint_source(dst)
    max_mae = max_changed = 0.0
    pixels_sampled = rendered_pixels = 0
    text_equal = True
    with fitz.open(src) as original, fitz.open(dst) as optimized:
        if original.needs_pass or optimized.needs_pass:
            raise ValueError('PDF protégé non auditable')
        count = original.page_count
        if count < 1 or count != optimized.page_count or count > max_pages:
            raise ValueError('Nombre de pages invalide ou budget de pages dépassé')
        # Preflight every page before the first rendering to avoid partial audits.
        for index in range(count):
            a, b = original[index], optimized[index]
            if _geometry(a) != _geometry(b):
                raise RuntimeError(f'Géométrie modifiée page {index + 1}')
            for page in (a, b):
                bounds = page.rect
                pixels = (bounds.width * scale + 2) * (bounds.height * scale + 2)
                if bounds.is_empty or bounds.is_infinite or pixels > max_pixels_per_page:
                    raise ValueError('Budget de pixels par page dépassé avant rendu')
                rendered_pixels += math.ceil(pixels)
                if rendered_pixels > max_total_pixels:
                    raise ValueError('Budget de pixels total dépassé avant rendu')
        for index in range(count):
            a, b = original[index], optimized[index]
            if a.get_text('text') != b.get_text('text'):
                text_equal = False
            before = _pixmap(a, scale, max_pixels_per_page)
            after = _pixmap(b, scale, max_pixels_per_page)
            if (before.width, before.height, before.n) != (after.width, after.height, after.n):
                raise RuntimeError(f'Dimensions du rendu modifiées page {index + 1}')
            left, right = memoryview(before.samples), memoryview(after.samples)
            total = changed = samples = 0
            for y in range(0, before.height, sample_step):
                for x in range(0, before.width, sample_step):
                    i, j = y * before.stride + 3*x, y * after.stride + 3*x
                    diff = (abs(left[i]-right[j]) + abs(left[i+1]-right[j+1])
                            + abs(left[i+2]-right[j+2]))
                    total += diff
                    changed += diff > 3 * pixel_delta
                    samples += 1
            if not samples:
                raise RuntimeError('Aucun pixel échantillonné')
            pixels_sampled += samples
            max_mae = max(max_mae, total / (3 * samples))
            max_changed = max(max_changed, changed / samples)
    verify_source_unchanged(src, source_before)
    verify_source_unchanged(dst, candidate_before)
    return CompressionVisualAudit(
        count, pixels_sampled, round(max_mae, 4), round(max_changed, 6),
        text_equal, True, source_before.sha256, candidate_before.sha256,
        float(scale), sample_step, pixel_delta)
