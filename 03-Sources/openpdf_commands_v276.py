"""UI-independent command dispatch with explicit busy policy. Abdelhalim Talbi."""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Command:
    key: str
    label: str
    method: str
    requires_idle: bool = False

COMMANDS = (
    Command('add', 'Ajouter', 'add_files', True),
    Command('edit', 'Éditer les pages', 'open_preview', True),
    Command('save', 'Enregistrer', '_save_editor', True),
    Command('merge', 'Fusionner', '_merge', True),
    Command('compress', 'Compresser', '_compress', True),
    Command('split', 'Découper', '_split', True),
)

class CommandRouter:
    def __init__(self, target, is_busy: Callable[[], bool]):
        self.target = target
        self.is_busy = is_busy
        self.commands = {item.key: item for item in COMMANDS}

    def dispatch(self, key):
        if key not in self.commands:
            raise KeyError(f'Commande inconnue : {key}')
        cmd = self.commands[key]
        if cmd.requires_idle and self.is_busy():
            return False
        method = getattr(self.target, cmd.method)
        method()
        return True
