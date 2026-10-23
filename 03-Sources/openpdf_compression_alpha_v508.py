"""V50.8: independently verify PDF alpha/transparency before compression publication.

RGB-on-white comparisons cannot detect loss of transparency. Compare every
rendered alpha sample at the configured bounded scale, including annotations,
without modifying either PDF. This is not a PDF/A, print, OCR or high-resolution
transparency certification.

Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_alpha_fidelity(source, candidate, policy, *, source_sha256, candidate_sha256):
    """Reject any changed alpha pixel; return evidence bound to exact PDF bytes.

    The complete page geometry and pixel budget are checked before rendering.
    Alpha is checked at policy.render_scale, not at native print resolution.
    """
    from openpdf_compression_acceptance_v489 import AcceptancePolicy
    if type(policy) is not AcceptancePolicy:
        raise TypeError('Expected AcceptancePolicy')
    for name, value in (('source_sha256', source_sha256),
                        ('candidate_sha256', candidate_sha256)):
        if (type(value) is not str or len(value) != 64 or
                any(char not in '0123456789abcdef' for char in value)):
            raise ValueError(f'Invalid {name}')
    src, dst = Path(source), Path(candidate)
    if (src.is_symlink() or dst.is_symlink() or not src.is_file() or
            not dst.is_file() or src.resolve() == dst.resolve()):
        raise RuntimeError('Distinct regular PDFs required for alpha verification')
    if _sha256(src) != source_sha256 or _sha256(dst) != candidate_sha256:
        raise RuntimeError('Alpha audit input hash disagrees with receipt')

    import fitz
    try:
        with fitz.open(src) as before, fitz.open(dst) as after:
            if before.needs_pass or after.needs_pass:
                raise RuntimeError('Encrypted PDF cannot be alpha-verified')
            pages = before.page_count
            if not 1 <= pages <= policy.max_pages or pages != after.page_count:
                raise RuntimeError('Alpha audit PDF page count differs or exceeds budget')
            matrix = fitz.Matrix(policy.render_scale, policy.render_scale)
            planned = 0
            for index in range(pages):
                a, b = before[index], after[index]
                ga = (tuple(round(float(x), 4) for x in a.mediabox),
                      tuple(round(float(x), 4) for x in a.cropbox), a.rotation)
                gb = (tuple(round(float(x), 4) for x in b.mediabox),
                      tuple(round(float(x), 4) for x in b.cropbox), b.rotation)
                if ga != gb:
                    raise RuntimeError(f'Alpha audit page {index + 1} geometry differs')
                bounds = a.rect
                if (bounds.is_empty or bounds.is_infinite or bounds.width <= 0 or
                        bounds.height <= 0 or not math.isfinite(bounds.width * bounds.height)):
                    raise RuntimeError('Invalid alpha audit page geometry')
                estimate = math.ceil((bounds.width * policy.render_scale + 2) *
                                     (bounds.height * policy.render_scale + 2))
                if estimate > policy.max_pixels_per_page:
                    raise RuntimeError('Alpha audit page pixel budget exceeded')
                planned += estimate
                if planned > policy.max_total_pixels:
                    raise RuntimeError('Alpha audit total pixel budget exceeded')

            pixels = transparent = translucent = opaque = 0
            for index in range(pages):
                a = before[index].get_pixmap(matrix=matrix, colorspace=fitz.csRGB,
                                             alpha=True, annots=True)
                b = after[index].get_pixmap(matrix=matrix, colorspace=fitz.csRGB,
                                            alpha=True, annots=True)
                if ((a.width, a.height, a.n) != (b.width, b.height, b.n) or
                        a.n != 4 or a.width * a.height > policy.max_pixels_per_page):
                    raise RuntimeError(f'Alpha audit page {index + 1} raster differs')
                left, right = memoryview(a.samples), memoryview(b.samples)
                for row in range(a.height):
                    lo, ro = row * a.stride, row * b.stride
                    alpha_a = left[lo + 3:lo + a.width * 4:4]
                    alpha_b = right[ro + 3:ro + b.width * 4:4]
                    if alpha_a != alpha_b:
                        raise RuntimeError(f'Alpha channel differs on page {index + 1}')
                    opaque += sum(value == 255 for value in alpha_a)
                    transparent += sum(value == 0 for value in alpha_a)
                    translucent += sum(0 < value < 255 for value in alpha_a)
                pixels += a.width * a.height
                if pixels > policy.max_total_pixels:
                    raise RuntimeError('Alpha audit raster pixel budget exceeded')
    except (ValueError, fitz.FileDataError) as exc:
        raise RuntimeError('Unreadable PDF during alpha audit') from exc
    if _sha256(src) != source_sha256 or _sha256(dst) != candidate_sha256:
        raise RuntimeError('PDF changed during alpha verification')
    if transparent + translucent + opaque != pixels:
        raise RuntimeError('Alpha audit accounting mismatch')
    return {
        'pages_verified': pages, 'pixels_verified': pixels,
        'transparent_pixels': transparent, 'translucent_pixels': translucent,
        'opaque_pixels': opaque, 'alpha_mismatch_pixels': 0,
        'source_sha256': source_sha256, 'candidate_sha256': candidate_sha256,
        'render_scale': policy.render_scale,
        'method': 'full_alpha_channel_at_bounded_render_scale',
        'limit': 'not_print_or_high_resolution_transparency_certification',
    }
