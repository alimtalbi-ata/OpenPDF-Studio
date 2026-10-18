"""Idempotent toolbar and keyboard command policies. Abdelhalim Talbi."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Shortcut:
    sequence: str
    command: str

SHORTCUTS = (Shortcut('<Control-o>', 'add'), Shortcut('<Control-s>', 'save'), Shortcut('<Control-Shift-m>', 'merge'), Shortcut('<Control-Shift-c>', 'compress'), Shortcut('<Control-Shift-d>', 'split'))

def validate_shortcuts(shortcuts, command_keys):
    seen = set()
    for item in shortcuts:
        if item.sequence in seen:
            raise ValueError('Duplicate shortcut: ' + item.sequence)
        if item.command not in command_keys:
            raise ValueError('Unknown shortcut command: ' + item.command)
        seen.add(item.sequence)
    return tuple(shortcuts)

def command_enabled(command, busy):
    return not (busy and command.requires_idle)
