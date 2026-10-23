"""V51.0: detect image-only PDF pages before editable Office conversion.

This is a conservative raster coverage heuristic, NOT OCR, image recognition,
or a claim of Office layout fidelity. No PDF text is logged or persisted.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import hashlib
import json
import math

import fitz

MAX_PAGES = 5000
MAX_IMAGE_RECTS_PER_PAGE = 512
DEFAULT_RASTER_THRESHOLD = 0.65


class ScannedPDFRequiresOCRError(ValueError):
    """An image-only page would otherwise be silently lost in Office output."""


@dataclass(frozen=True)
class OfficeScanReport:
    schema: str
    source_sha256: str
    page_count: int
    pages: tuple[dict, ...]
    scanned_pages: tuple[int, ...]
    non_text_graphics_pages: tuple[int, ...]
    blank_pages: tuple[int, ...]
    limitation: str = 'raster_coverage_heuristic_not_ocr_or_office_layout_certification'

    def as_dict(self):
        data = asdict(self)
        for key in ('pages', 'scanned_pages', 'non_text_graphics_pages', 'blank_pages'):
            data[key] = list(data[key])
        return data


def _union_area(rectangles):
    """Exact area of the union of bounded axis-aligned rectangles."""
    if not rectangles:
        return 0.0
    xs = sorted({v for x0, _, x1, _ in rectangles for v in (x0, x1)})
    area = 0.0
    for left, right in zip(xs, xs[1:]):
        if right <= left:
            continue
        intervals = sorted((y0, y1) for x0, y0, x1, y1 in rectangles
                           if x0 < right and x1 > left)
        if not intervals:
            continue
        low, high = intervals[0]
        covered = 0.0
        for y0, y1 in intervals[1:]:
            if y0 > high:
                covered += high - low
                low, high = y0, y1
            else:
                high = max(high, y1)
        covered += high - low
        area += (right - left) * covered
    return area


def _raster_coverage(page):
    bounds = page.rect
    if not all(math.isfinite(x) for x in (bounds.x0, bounds.y0, bounds.x1, bounds.y1)):
        raise ValueError('PDF page geometry is invalid')
    if bounds.width <= 0 or bounds.height <= 0:
        raise ValueError('PDF page geometry is empty')
    images = page.get_image_info()
    if len(images) > MAX_IMAGE_RECTS_PER_PAGE:
        raise ValueError('Too many raster image rectangles for a safe Office preflight')
    rects = []
    for item in images:
        rect = fitz.Rect(item['bbox']) & bounds
        if rect.is_empty or rect.is_infinite:
            continue
        if not all(math.isfinite(v) for v in (rect.x0, rect.y0, rect.x1, rect.y1)):
            raise ValueError('PDF raster geometry is invalid')
        rects.append((rect.x0, rect.y0, rect.x1, rect.y1))
    coverage = _union_area(rects) / (bounds.width * bounds.height)
    return round(min(1.0, max(0.0, coverage)), 6), len(images)


def assess_office_source(source, *, raster_threshold=DEFAULT_RASTER_THRESHOLD):
    """Return a metadata-only report, without modifying the PDF or output path.

    A page with no extractable text and >=65% raster coverage is classified
    scanned; blank pages remain supported for backward compatibility.
    """
    if not 0.0 < raster_threshold <= 1.0:
        raise ValueError('Invalid raster threshold')
    source = Path(source)
    if not source.is_file() or source.suffix.lower() != '.pdf' or source.is_symlink():
        raise ValueError('Invalid PDF source')
    with source.open('rb') as handle:
        original_digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    records, scanned, graphics, blank = [], [], [], []
    with fitz.open(source) as doc:
        if doc.needs_pass:
            raise ValueError('Encrypted PDF: Office conversion unavailable')
        if not 0 < len(doc) <= MAX_PAGES:
            raise ValueError('PDF page count outside safe limits')
        for page_number, page in enumerate(doc, 1):
            text_present = bool(page.get_text('text', sort=True).strip())
            coverage, image_count = _raster_coverage(page)
            if text_present:
                kind = 'extractable_text'
            elif coverage >= raster_threshold:
                kind = 'scanned_image_only'
                scanned.append(page_number)
            elif image_count or page.get_drawings():
                kind = 'graphics_without_extractable_text'
                graphics.append(page_number)
            else:
                kind = 'blank'
                blank.append(page_number)
            records.append(dict(page=page_number, classification=kind,
                                raster_coverage=coverage, raster_images=image_count,
                                has_extractable_text=text_present))
    with source.open('rb') as handle:
        if hashlib.file_digest(handle, 'sha256').hexdigest() != original_digest:
            raise RuntimeError('PDF changed during Office scan preflight')
    return OfficeScanReport('openpdf.office.scan-preflight.v51.0', original_digest,
                            len(records), tuple(records), tuple(scanned),
                            tuple(graphics), tuple(blank))


def require_editable_source(report):
    if report.scanned_pages:
        pages = ', '.join(str(n) for n in report.scanned_pages[:20])
        if len(report.scanned_pages) > 20:
            pages += ', ...'
        raise ScannedPDFRequiresOCRError(
            f'OCR required before editable Office conversion: image-only PDF page(s) {pages}')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Office scan preflight (no OCR, no PDF changes)')
    parser.add_argument('source', type=Path)
    args = parser.parse_args(argv)
    report = assess_office_source(args.source)
    print(json.dumps({**report.as_dict(), 'editable_text_gate':
                      'blocked_ocr_required' if report.scanned_pages else 'passed'},
                     ensure_ascii=False, indent=2))
    return 2 if report.scanned_pages else 0


if __name__ == '__main__':
    raise SystemExit(main())
