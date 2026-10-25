"""V50.6: bind measured RGB acceptance to actual compressed bytes.

Reject missing, inconsistent or forged quality receipts before publication.
This is bounded-scale raster evidence, not a PDF/A or print certification.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations
from dataclasses import asdict
import math


def verified_evidence(receipt, *, source_sha256, source_bytes, candidate_sha256,
                      candidate_bytes, profile, policy):
    """Validate the canonical engine's quality receipt against file digests.

    This function does not render again: the engine already rendered every RGB
    pixel and checked text/geometry/structure before creating its receipt.
    """
    metrics = getattr(receipt, 'metrics', None)
    audit = getattr(metrics, 'visual_audit', None)
    if (not getattr(receipt, 'published', False) or metrics is None
            or not isinstance(audit, dict) or audit.get('accepted') is not True):
        raise RuntimeError('Missing accepted full-RGB compression evidence')
    if (getattr(receipt, 'visual_audit', None) != audit
            or metrics.published is not True or metrics.profile != profile
            or metrics.source_sha256 != source_sha256
            or metrics.source_bytes != source_bytes
            or metrics.output_bytes != candidate_bytes
            or receipt.sha256 != candidate_sha256 or receipt.size != candidate_bytes):
        raise RuntimeError('Compression receipt and file identity disagree')
    expected = {
        'source_sha256': source_sha256,
        'candidate_sha256': candidate_sha256,
        'source_bytes': source_bytes,
        'candidate_bytes': candidate_bytes,
        'policy': asdict(policy),
        'evidence': 'full_rgb_pixels_at_bounded_scale_not_archival_or_print_certification',
    }
    if any(audit.get(key) != value for key, value in expected.items()):
        raise RuntimeError('RGB audit does not match source, candidate or policy')
    pages, pixels = audit.get('pages_compared'), audit.get('pixels_compared')
    if (type(pages) is not int or not 1 <= pages <= policy.max_pages
            or type(pixels) is not int or not 1 <= pixels <= policy.max_total_pixels):
        raise RuntimeError('Invalid full-RGB measurement coverage')
    for key, maximum in (('max_page_mae', policy.max_page_mae),
                         ('max_page_changed_fraction', policy.max_page_changed_fraction)):
        value = audit.get(key)
        if (type(value) not in (int, float) or not math.isfinite(value)
                or not 0 <= value <= maximum + 1e-8):
            raise RuntimeError('RGB quality measurement missing or above threshold')
    # V538: bind the structure audit to the accepted size/visual receipt.
    # A missing or incomplete structure audit is never a verified gain.
    structure = audit.get('structure')
    required = ('pages_verified', 'links_verified', 'annotations_verified',
                'widgets_verified', 'attachments_verified', 'bookmarks_verified',
                'layers_verified')
    if (not isinstance(structure, dict)
            or any(type(structure.get(key)) is not int for key in required)
            or structure['pages_verified'] != pages
            or any(structure[key] < 0 for key in required[1:])):
        raise RuntimeError('Missing or invalid PDF semantic structure evidence')
    saving = 100 * (source_bytes - candidate_bytes) / source_bytes
    reported = audit.get('saving_percent')
    if (type(reported) not in (int, float) or not math.isfinite(reported)
            or abs(reported - saving) > 0.00011
            or saving + 1e-10 < policy.min_saving_percent):
        raise RuntimeError('Compression saving evidence inconsistent')
    return {
        'pages_compared': pages,
        'pixels_compared': pixels,
        'structure': {key: structure[key] for key in required},
        'max_page_mae': audit['max_page_mae'],
        'max_page_changed_fraction': audit['max_page_changed_fraction'],
        'render_scale': policy.render_scale,
        'pixel_delta': policy.pixel_delta,
        'evidence': audit['evidence'],
    }
