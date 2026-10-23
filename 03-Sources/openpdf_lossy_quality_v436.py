"""Bounded render fidelity checks for lossy PDF image compression (V43.8).

Every page is rendered at a controlled resolution. Global and spatial-tile
metrics detect both broad drift and local damage hidden by a page-wide mean.
These screening metrics do NOT certify OCR accuracy, accessibility or identity.
Author: Abdelhalim Talbi.
"""
from dataclasses import dataclass
import math
import fitz


@dataclass(frozen=True)
class PageQuality:
    page: int
    samples: int
    mean_absolute_error: float
    changed_fraction: float
    worst_tile_mae: float
    worst_tile_changed_fraction: float
    tiles_checked: int


def _boxes(page):
    return (tuple(round(float(v), 4) for v in page.mediabox),
            tuple(round(float(v), 4) for v in page.cropbox),
            int(page.rotation))


def _render(page, scale, max_pixels):
    bounds = page.rect
    if bounds.is_empty or bounds.is_infinite:
        raise ValueError('Géométrie PDF invalide')
    if (bounds.width * scale + 2) * (bounds.height * scale + 2) > max_pixels:
        raise ValueError('Page trop grande pour la mesure de qualité')
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                          colorspace=fitz.csRGB, alpha=False, annots=True)
    if pix.width * pix.height > max_pixels or pix.n != 3:
        raise ValueError('Rendu trop volumineux ou format couleur inattendu')
    return pix


def _compare_rgb(before, after, *, sample_step, pixel_delta, tile_grid,
                 min_tile_samples):
    if (before.width, before.height, before.n) != (after.width, after.height, after.n):
        raise RuntimeError('Dimensions de rendu différentes : sortie rejetée')
    a, b = memoryview(before.samples), memoryview(after.samples)
    absolute_sum = changed = samples = 0
    # Fixed upper bound: at most tile_grid**2 tile counters per page.
    tiles = [[0, 0, 0] for _ in range(tile_grid * tile_grid)]
    for y in range(0, before.height, sample_step):
        row_a, row_b = y * before.stride, y * after.stride
        tile_y = min(tile_grid - 1, y * tile_grid // before.height)
        for x in range(0, before.width, sample_step):
            i, j = row_a + x * 3, row_b + x * 3
            delta = abs(a[i] - b[j]) + abs(a[i+1] - b[j+1]) + abs(a[i+2] - b[j+2])
            altered = int(delta > 3 * pixel_delta)
            absolute_sum += delta
            changed += altered
            samples += 1
            tile_x = min(tile_grid - 1, x * tile_grid // before.width)
            bucket = tiles[tile_y * tile_grid + tile_x]
            bucket[0] += delta
            bucket[1] += altered
            bucket[2] += 1
    if not samples:
        raise ValueError('Échantillonnage de rendu vide')
    eligible = [t for t in tiles if t[2] >= min_tile_samples]
    # V43.8: a configuration with zero populated tiles previously returned
    # worst_tile_mae=0 and silently disabled the regional safety gate.
    # Never certify an unmeasured local metric.
    if not eligible:
        raise RuntimeError(
            'Contrôle qualité local impossible : aucune zone assez échantillonnée; '
            'réduire min_tile_samples ou sample_step'
        )
    worst_mae = max((t[0] / (3 * t[2]) for t in eligible), default=0.0)
    worst_changed = max((t[1] / t[2] for t in eligible), default=0.0)
    return (samples, absolute_sum / (samples * 3), changed / samples,
            worst_mae, worst_changed, len(eligible))


def validate_lossy_render(source, candidate, *, scale=0.75, sample_step=3,
                          max_pixels=12_000_000, max_mae=12.0,
                          max_changed_fraction=0.35, pixel_delta=24,
                          tile_grid=12, min_tile_samples=16,
                          max_tile_mae=38.0,
                          max_tile_changed_fraction=0.65):
    """Reject a candidate on global OR localized image-render divergence.

    max_tile_mae measures the highest RGB channel error across sufficiently
    populated tiles; unlike a global average, it catches a small damaged area.
    Sampling may still miss tiny glyphs or security-sensitive changes.
    """
    if (not isinstance(scale, (int, float)) or isinstance(scale, bool)
            or not math.isfinite(scale) or not 0.25 <= scale <= 2
            or not isinstance(sample_step, int) or isinstance(sample_step, bool)
            or not 1 <= sample_step <= 32
            or not isinstance(max_pixels, int) or isinstance(max_pixels, bool)
            or not 10_000 <= max_pixels <= 12_000_000
            or not isinstance(max_mae, (int, float)) or isinstance(max_mae, bool)
            or not math.isfinite(max_mae) or not 0 <= max_mae <= 255
            or not isinstance(max_changed_fraction, (int, float))
            or isinstance(max_changed_fraction, bool)
            or not math.isfinite(max_changed_fraction) or not 0 <= max_changed_fraction <= 1
            or not isinstance(pixel_delta, (int, float)) or isinstance(pixel_delta, bool)
            or not math.isfinite(pixel_delta) or not 0 <= pixel_delta <= 255
            or not isinstance(tile_grid, int) or isinstance(tile_grid, bool)
            or not 1 <= tile_grid <= 16
            or not isinstance(min_tile_samples, int) or isinstance(min_tile_samples, bool)
            or not 1 <= min_tile_samples <= 4096
            or not isinstance(max_tile_mae, (int, float)) or isinstance(max_tile_mae, bool)
            or not math.isfinite(max_tile_mae) or not 0 <= max_tile_mae <= 255
            or not isinstance(max_tile_changed_fraction, (int, float))
            or isinstance(max_tile_changed_fraction, bool)
            or not math.isfinite(max_tile_changed_fraction)
            or not 0 <= max_tile_changed_fraction <= 1):
        raise ValueError('Paramètres de contrôle qualité invalides')
    reports = []
    with fitz.open(source) as original, fitz.open(candidate) as output:
        if original.needs_pass or output.needs_pass:
            raise ValueError('PDF protégé')
        if original.page_count < 1 or original.page_count != output.page_count:
            raise ValueError('Nombre de pages modifié ou PDF vide')
        for index in range(original.page_count):
            page_a, page_b = original[index], output[index]
            if _boxes(page_a) != _boxes(page_b):
                raise RuntimeError(f'Géométrie modifiée à la page {index + 1} : sortie rejetée')
            pix_a = _render(page_a, scale, max_pixels)
            pix_b = _render(page_b, scale, max_pixels)
            samples, mae, changed, tile_mae, tile_changed, tiles = _compare_rgb(
                pix_a, pix_b, sample_step=sample_step, pixel_delta=pixel_delta,
                tile_grid=tile_grid, min_tile_samples=min_tile_samples)
            reports.append(PageQuality(index + 1, samples, round(mae, 4),
                                       round(changed, 6), round(tile_mae, 4),
                                       round(tile_changed, 6), tiles))
            if (mae > max_mae or changed > max_changed_fraction
                    or tile_mae > max_tile_mae
                    or tile_changed > max_tile_changed_fraction):
                raise RuntimeError(
                    f'Qualité visuelle insuffisante page {index + 1} : '
                    f'MAE={mae:.2f}/255, pixels altérés={changed:.1%}, '
                    f'MAE locale max={tile_mae:.2f}/255, '
                    f'pixels altérés locaux max={tile_changed:.1%}; sortie rejetée'
                )
    return {'pages_verified': len(reports),
            'max_mae': max(r.mean_absolute_error for r in reports),
            'max_changed_fraction': max(r.changed_fraction for r in reports),
            'max_tile_mae': max(r.worst_tile_mae for r in reports),
            'max_tile_changed_fraction': max(r.worst_tile_changed_fraction for r in reports),
            'tiles_checked': sum(r.tiles_checked for r in reports),
            'sampled_pixels': sum(r.samples for r in reports),
            'scale': scale, 'sample_step': sample_step, 'tile_grid': tile_grid,
            'min_tile_samples': min_tile_samples,
            'max_tile_changed_fraction_allowed': max_tile_changed_fraction}
