"""V27.0 presentation controller: single-source navigation and action routing.

No PDF processing or Tk widget is performed in this module. This allows
headless tests and incremental removal of inherited GUI implementations.
Author: Abdelhalim Talbi.
"""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class WorkspaceAction:
    label: str
    handler: str
    shortcut: str = ""

ACTIONS = (
    WorkspaceAction("Ajouter", "add_files", "Ctrl+O"),
    WorkspaceAction("Éditer les pages", "open_preview"),
    WorkspaceAction("Enregistrer", "_save_editor", "Ctrl+S"),
    WorkspaceAction("Fusionner", "_merge"),
    WorkspaceAction("Compresser", "_compress"),
    WorkspaceAction("Découper", "_split"),
)
OPERATIONS_BY_ACTION = {
    "_merge": "Fusionner des PDF",
    "_compress": "Compresser / optimiser",
    "_split": "Découper en pages",
}

class WorkspaceController:
    """Pure navigation state; legacy listbox is a temporary compatibility view."""
    def __init__(self):
        self.documents = []
        self.selected_index = None

    def replace(self, paths):
        self.documents = [str(Path(p)) for p in paths]
        self.selected_index = 0 if self.documents else None

    def select(self, index):
        if not isinstance(index, int) or not 0 <= index < len(self.documents):
            raise IndexError("document selection outside workspace")
        self.selected_index = index
        return self.documents[index]

    def selected(self):
        if self.selected_index is None:
            return None
        return self.documents[self.selected_index]
