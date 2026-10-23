"""Bounded, metadata-only compression preflight before any PDF image decode.

Rejects unexpectedly large page/image resources *before* allocating a private
candidate or invoking the compressor. Limits are intentionally conservative,
not a PDF malware scanner or a substitute for runtime process isolation.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import fitz


@dataclass(frozen=True)
class CompressionResourceLimits:
    max_source_bytes: int = 2 * 1024 * 1024 * 1024
    max_pages: int = 2000
    max_page_dimension_pt: float = 14400.0
    max_image_pixels: int = 120_000_000
    max_total_unique_image_pixels: int = 1_000_000_000
    max_unique_images: int = 20_000
    # V47.7: also bound *displayed* image occurrences. This includes inline BI
    # images that are not listed by page.get_images(full=True), and repeated
    # uses of the same XREF. This intentionally counts repetitions.
    max_image_appearances: int = 50_000
    max_total_appearance_pixels: int = 2_000_000_000


def _validate_limits(limits):
    if type(limits) is not CompressionResourceLimits:
        raise ValueError('Politique de ressources de compression invalide')
    for name in ('max_source_bytes', 'max_pages', 'max_image_pixels',
                 'max_total_unique_image_pixels', 'max_unique_images',
                 'max_image_appearances', 'max_total_appearance_pixels'):
        value = getattr(limits, name)
        if type(value) is not int or value < 1:
            raise ValueError(f'Budget de compression invalide : {name}')
    d = limits.max_page_dimension_pt
    if isinstance(d, bool) or not isinstance(d, (int, float)) or not math.isfinite(d) or d <= 0:
        raise ValueError('Dimension maximale de page invalide')
    return limits


def _image_dimension(document, xref, key):
    kind, value = document.xref_get_key(xref, key)
    if kind != 'int':
        raise RuntimeError(f'Image PDF sans dimension entière {key} (xref {xref})')
    try:
        dimension = int(value)
    except (ValueError, TypeError) as exc:
        raise RuntimeError(f'Dimension image PDF invalide (xref {xref})') from exc
    if dimension < 1:
        raise RuntimeError(f'Dimension image PDF non positive (xref {xref})')
    return dimension


def preflight_compression_source(source, *, limits=CompressionResourceLimits()):
    """Return resource estimates without decoding images or rendering pages.

    Counts each unique image XREF once even when reused on many pages.
    Rejections occur before any temporary output or compressor invocation.
    """
    _validate_limits(limits)
    path = Path(source)
    if not path.is_file():
        raise ValueError('PDF source inexistant')
    size = path.stat().st_size
    if size < 1 or size > limits.max_source_bytes:
        raise RuntimeError('Budget de taille du PDF source dépassé')
    seen = set()
    total_pixels = 0
    appearance_count = 0
    appearance_pixels = 0
    with fitz.open(str(path)) as document:
        if document.needs_pass:
            raise RuntimeError('PDF chiffré : compression refusée')
        pages = document.page_count
        if not 1 <= pages <= limits.max_pages:
            raise RuntimeError('Budget de pages PDF dépassé')
        for index in range(pages):
            page = document[index]
            bounds = page.rect
            if (bounds.is_empty or bounds.is_infinite
                    or not all(math.isfinite(float(x)) for x in bounds)
                    or bounds.width <= 0 or bounds.height <= 0
                    or bounds.width > limits.max_page_dimension_pt
                    or bounds.height > limits.max_page_dimension_pt):
                raise RuntimeError(f'Dimensions de page hors budget : {index + 1}')
            for item in page.get_images(full=True):
                xref = item[0]
                if type(xref) is not int or xref < 1:
                    raise RuntimeError('Référence image PDF invalide')
                if xref in seen:
                    continue
                seen.add(xref)
                if len(seen) > limits.max_unique_images:
                    raise RuntimeError('Budget de ressources image PDF dépassé')
                width = _image_dimension(document, xref, 'Width')
                height = _image_dimension(document, xref, 'Height')
                pixels = width * height
                if pixels > limits.max_image_pixels:
                    raise RuntimeError('Budget de pixels par image PDF dépassé')
                total_pixels += pixels
                if total_pixels > limits.max_total_unique_image_pixels:
                    raise RuntimeError('Budget cumulé de pixels image PDF dépassé')
            # get_images() only enumerates XREF-backed image resources and
            # misses inline BI images. get_image_info(xrefs=False) inspects
            # displayed image metadata without requesting image binary extraction
            # or rasterizing the page. Count all appearances conservatively:
            # a repeated XREF can still increase processing cost.
            for info in page.get_image_info(xrefs=False):
                width = info.get('width')
                height = info.get('height')
                if (type(width) is not int or type(height) is not int
                        or width < 1 or height < 1):
                    raise RuntimeError('Dimensions d’image affichée invalides')
                pixels = width * height
                if pixels > limits.max_image_pixels:
                    raise RuntimeError('Budget de pixels par image affichée dépassé')
                appearance_count += 1
                if appearance_count > limits.max_image_appearances:
                    raise RuntimeError('Budget d’occurrences d’images dépassé')
                appearance_pixels += pixels
                if appearance_pixels > limits.max_total_appearance_pixels:
                    raise RuntimeError('Budget de pixels des images affichées dépassé')
    return {
        'pages': pages, 'source_bytes': size,
        'unique_images': len(seen), 'unique_image_pixels': total_pixels,
        'image_appearances': appearance_count,
        'appearance_pixels': appearance_pixels,
        'evidence': 'metadata_preflight_not_runtime_isolation',
    }
