"""Stable user-facing compression quality presets (no GUI dependency).

A sampled audit is not proof of complete document fidelity. The strict
preset compares every rendered pixel at the chosen render scale.
Author: Abdelhalim Talbi.
"""
from openpdf_compression_quality_gate_v470 import CompressionQualityGate

QUALITY_MODES = (
    'Sans audit (rapide)',
    'Mesurer sans bloquer',
    'Équilibré (MAE ≤ 4, pixels ≤ 2 %)',
    'Strict (pixels identiques)',
)

def resolve_quality_mode(mode):
    """Return (measure_visual, gate) without relying on Tkinter."""
    if type(mode) is not str or mode not in QUALITY_MODES:
        raise ValueError('Mode de contrôle qualité inconnu')
    if mode == QUALITY_MODES[0]:
        return False, None
    if mode == QUALITY_MODES[1]:
        return True, None
    if mode == QUALITY_MODES[2]:
        return False, CompressionQualityGate(4.0, 0.02, 0.5, 2, 12)
    return False, CompressionQualityGate(0.0, 0.0, 0.5, 1, 0)
