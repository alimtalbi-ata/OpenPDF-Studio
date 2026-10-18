"""Declarative layout helpers without a Tk runtime dependency. Abdelhalim Talbi."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Panel:
    key: str
    title: str

PANELS = (Panel('pages', 'Éditeur de pages'), Panel('tools', 'Outils PDF'), Panel('properties', 'Propriétés'))

def unique_commands(commands):
    """Reject duplicate commands before creating widgets."""
    keys = [command.key for command in commands]
    if len(keys) != len(set(keys)):
        raise ValueError('Identifiants de commandes dupliqués')
    return tuple(commands)

def normalize_progress(progress):
    """Convert fractional progress to a safe integer percentage."""
    try:
        value = float(progress)
    except (TypeError, ValueError):
        return 0
    if value != value: return 0
    return max(0, min(100, round(value * 100)))
