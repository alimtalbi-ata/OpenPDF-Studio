"""Human-readable compression measurements, without claiming PDF certification.

Pure presentation helper: no GUI dependency, no PDF reads or side effects.
Author: Abdelhalim Talbi. OpenPDF Studio V49.0.
"""
from __future__ import annotations


def _size(n):
    if type(n) is not int or n < 0:
        raise ValueError('Taille de compression invalide')
    return f'{n:,}'.replace(',', ' ') + ' octets'


def format_compression_result(receipt):
    """Show measured bytes, saving, and bounded RGB evidence if available."""
    metrics = getattr(receipt, 'metrics', None)
    if metrics is None:
        return str(receipt)
    if not getattr(receipt, 'published', False):
        return 'Aucun fichier publié : ' + str(getattr(receipt, 'message', 'Aucun gain'))
    src = metrics.source_bytes
    dst = metrics.output_bytes
    delta = src - dst
    label = 'gain mesuré' if delta >= 0 else 'augmentation mesurée'
    text = (f'Compression publiée : {_size(src)} → {_size(dst)} ; '
            f'{label} : {abs(metrics.saving_percent):.2f} % '
            f'({_size(abs(delta))}).')
    audit = getattr(metrics, 'visual_audit', None)
    full = None
    if isinstance(audit, dict):
        full = audit.get('full_pixel_acceptance', audit)
    if isinstance(full, dict) and full.get('accepted') is True and full.get('evidence') == 'full_rgb_pixels_at_bounded_scale_not_archival_or_print_certification':
        policy = full.get('policy', {})
        scale = policy.get('render_scale', 'inconnue') if isinstance(policy, dict) else 'inconnue'
        text += (f' Audit RGB intégral : {full["pages_compared"]} page(s), '
                 f'{full["pixels_compared"]:,} pixels à échelle {scale} ; '
                 f'MAE max {full["max_page_mae"]:.3f}/255 ; '
                 f'pixels modifiés {full["max_page_changed_fraction"]:.2%}. '
                 'Contrôle borné, pas une certification PDF/print/OCR.')
    elif audit is not None:
        text += ' Audit visuel par échantillonnage effectué (voir reçu technique).'
    return text
