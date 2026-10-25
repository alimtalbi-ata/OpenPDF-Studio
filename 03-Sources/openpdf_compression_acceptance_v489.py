"""Independent, read-only acceptance audit for PDF compression candidates.

Every rendered RGB pixel is compared at a bounded scale (no grid sampling).
V538 also enforces semantic fidelity of navigation, annotations, forms,
metadata and attachments using the existing production structure guard.
The report is evidence at the chosen scale, NOT archival, OCR or print fidelity.
Author: Abdelhalim Talbi. OpenPDF Studio V48.9.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path


class CompressionRejected(ValueError):
    """Compression candidate failed a required quality, size or safety check."""


@dataclass(frozen=True)
class AcceptancePolicy:
    min_saving_percent: float = 0.0
    max_page_mae: float = 4.0
    max_page_changed_fraction: float = 0.02
    render_scale: float = 0.5
    pixel_delta: int = 24
    max_pages: int = 500
    max_pixels_per_page: int = 2_000_000
    max_total_pixels: int = 15_000_000

    def __post_init__(self):
        for name, low, high in (
            ('min_saving_percent', 0, 100),
            ('max_page_mae', 0, 255),
            ('max_page_changed_fraction', 0, 1),
            ('render_scale', 0.25, 2.0),
        ):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'Invalid compression policy: {name}')
        for name, low, high in (
            ('pixel_delta', 0, 255), ('max_pages', 1, 10000),
            ('max_pixels_per_page', 10000, 12000000),
            ('max_total_pixels', 10000, 500000000),
        ):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'Invalid compression policy: {name}')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _geometry(page):
    return (tuple(round(float(v), 4) for v in page.mediabox),
            tuple(round(float(v), 4) for v in page.cropbox), int(page.rotation))


def _planned_pixels(page, scale):
    rect = page.rect
    if rect.is_empty or rect.is_infinite or not math.isfinite(rect.width * rect.height):
        raise CompressionRejected('Invalid page geometry')
    if rect.width <= 0 or rect.height <= 0:
        raise CompressionRejected('Invalid page dimensions')
    # Conservative renderer rounding margin; preflight BEFORE any allocation.
    return math.ceil((rect.width * scale + 2) * (rect.height * scale + 2))


def _measure_rgb(a, b, policy, fitz):
    matrix = fitz.Matrix(policy.render_scale, policy.render_scale)
    pix_a = a.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False, annots=True)
    pix_b = b.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False, annots=True)
    if (pix_a.width, pix_a.height, pix_a.n) != (pix_b.width, pix_b.height, pix_b.n):
        raise CompressionRejected('Rendered page geometry differs')
    if pix_a.n != 3 or pix_a.width * pix_a.height > policy.max_pixels_per_page:
        raise CompressionRejected('Rendered page exceeded pixel budget')
    left, right = memoryview(pix_a.samples), memoryview(pix_b.samples)
    total, changed = 0, 0
    for y in range(pix_a.height):
        offset_a, offset_b = y * pix_a.stride, y * pix_b.stride
        for x in range(pix_a.width):
            i, j = offset_a + x * 3, offset_b + x * 3
            r, g, bl = (abs(left[i+k] - right[j+k]) for k in range(3))
            total += r + g + bl
            changed += (r > policy.pixel_delta or g > policy.pixel_delta or bl > policy.pixel_delta)
    pixels = pix_a.width * pix_a.height
    return total / (3 * pixels), changed / pixels, pixels


def audit_compression_candidate(source, candidate, policy=AcceptancePolicy()):
    """Return an acceptance receipt; reject changed text/geometry, poor render or no gain.

    This read-only verifier is safe to use BEFORE any external publication step.
    It never certifies pixel equality above the chosen render scale.
    """
    if type(policy) is not AcceptancePolicy:
        raise TypeError('Expected AcceptancePolicy')
    import fitz
    src = Path(source).expanduser().resolve(strict=True)
    dst = Path(candidate).expanduser().resolve(strict=True)
    if src == dst or not src.is_file() or not dst.is_file():
        raise CompressionRejected('Distinct PDF files are required')
    source_size, candidate_size = src.stat().st_size, dst.stat().st_size
    if not source_size or not candidate_size:
        raise CompressionRejected('Empty PDF')
    src_hash, dst_hash = _sha256(src), _sha256(dst)
    saving_percent = 100 * (source_size - candidate_size) / source_size
    with fitz.open(src) as before, fitz.open(dst) as after:
        if before.needs_pass or after.needs_pass:
            raise CompressionRejected('Encrypted PDFs are not accepted')
        count = before.page_count
        if count < 1 or count > policy.max_pages or count != after.page_count:
            raise CompressionRejected('Page count differs or exceeds budget')
        planned = 0
        for index in range(count):
            a, b = before[index], after[index]
            if _geometry(a) != _geometry(b):
                raise CompressionRejected(f'Page {index+1}: geometry differs')
            for page in (a, b):
                pixels = _planned_pixels(page, policy.render_scale)
                if pixels > policy.max_pixels_per_page:
                    raise CompressionRejected('Per-page render budget exceeded')
                planned += pixels
                if planned > policy.max_total_pixels:
                    raise CompressionRejected('Total render budget exceeded')
        # V538: a perfectly identical RGB rendering can still conceal lost
        # hyperlinks, outlines, review annotations, forms or attachments.
        # Reuse the *production* structure guard before expensive rendering;
        # this independent audit must not certify a semantically broken PDF.
        from openpdf_structure_guard_v439 import validate_structure_preserved
        try:
            structure = validate_structure_preserved(src, dst)
        except (ValueError, RuntimeError, TypeError, KeyError) as exc:
            raise CompressionRejected('PDF semantic structure mismatch: ' + str(exc)) from exc
        max_mae = max_changed = 0.0
        compared = 0
        for index in range(count):
            a, b = before[index], after[index]
            if a.get_text('text') != b.get_text('text'):
                raise CompressionRejected(f'Page {index+1}: extractable text differs')
            mae, changed, pixels = _measure_rgb(a, b, policy, fitz)
            max_mae = max(max_mae, mae)
            max_changed = max(max_changed, changed)
            compared += pixels
            if mae > policy.max_page_mae or changed > policy.max_page_changed_fraction:
                raise CompressionRejected(f'Page {index+1}: visual quality below threshold')
    if _sha256(src) != src_hash or _sha256(dst) != dst_hash:
        raise CompressionRejected('File modified during audit')
    if saving_percent + 1e-10 < policy.min_saving_percent:
        raise CompressionRejected('Compression gain below required threshold')
    return {
        'accepted': True,
        'source_bytes': source_size,
        'candidate_bytes': candidate_size,
        'saved_bytes': source_size - candidate_size,
        'saving_percent': round(saving_percent, 4),
        'pages_compared': count,
        'pixels_compared': compared,
        'max_page_mae': round(max_mae, 6),
        'max_page_changed_fraction': round(max_changed, 8),
        'source_sha256': src_hash,
        'candidate_sha256': dst_hash,
        'structure': structure,
        'policy': asdict(policy),
        'evidence': 'full_rgb_pixels_at_bounded_scale_not_archival_or_print_certification',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only PDF compression size and quality acceptance')
    parser.add_argument('source')
    parser.add_argument('candidate')
    parser.add_argument('--min-saving-percent', type=float, default=0)
    parser.add_argument('--max-page-mae', type=float, default=4)
    parser.add_argument('--max-page-changed-fraction', type=float, default=0.02)
    parser.add_argument('--render-scale', type=float, default=0.5)
    args = parser.parse_args(argv)
    try:
        policy = AcceptancePolicy(min_saving_percent=args.min_saving_percent,
                                  max_page_mae=args.max_page_mae,
                                  max_page_changed_fraction=args.max_page_changed_fraction,
                                  render_scale=args.render_scale)
        result = audit_compression_candidate(args.source, args.candidate, policy)
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        print(json.dumps({'accepted': False, 'reason': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
