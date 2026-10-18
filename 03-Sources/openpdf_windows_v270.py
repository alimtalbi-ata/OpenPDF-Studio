"""OpenPDF Studio V27.0 — modular action controller and single navigator.

Legacy processing is deliberately retained until equivalent regression tests
exist; this release does not claim complete removal of V26.x inheritance.
Author: Abdelhalim Talbi.
"""
import tkinter as tk
from tkinter import ttk
from openpdf_windows_v269 import OpenPDFStudio as LegacyStudio
from openpdf_workspace_v270 import ACTIONS, OPERATIONS_BY_ACTION, WorkspaceController

class OpenPDFStudio(LegacyStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.0 — Abdelhalim Talbi')
        self.workspace_controller = WorkspaceController()
        self._install_workspace_commands()
        self.sidebar_files.bind('<<ListboxSelect>>', self._on_navigator_selection)
        self.bind('<Control-o>', lambda event: self.add_files())
        self.bind('<Control-s>', lambda event: self._save_editor())

    def _install_workspace_commands(self):
        # Replace the V26.7 duplicate quick toolbar with a declarative command bar.
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame) and child is not self.main_panes:
                buttons = [w.cget('text') for w in child.winfo_children() if isinstance(w, ttk.Button)]
                if 'Fusionner' in buttons and 'Compresser' in buttons:
                    child.destroy()
        bar = ttk.Frame(self, padding=(12, 5))
        bar.pack(fill='x', before=self.main_panes)
        for action in ACTIONS:
            ttk.Button(bar, text=action.label, command=lambda a=action: self._invoke_action(a.handler)).pack(side='left', padx=(0, 6))

    def _invoke_action(self, handler):
        if handler in OPERATIONS_BY_ACTION:
            self._choose_operation(OPERATIONS_BY_ACTION[handler])
        else:
            getattr(self, handler)()

    def _on_navigator_selection(self, event=None):
        selected = self.sidebar_files.curselection()
        if not selected:
            return
        self.workspace_controller.replace(self.files)
        index = selected[0]
        if index >= len(self.files):
            return
        self.workspace_controller.select(index)
        # Existing operations use filelist indices; keep this adapter in sync.
        self.filelist.selection_clear(0, 'end')
        self.filelist.selection_set(index)
        self._update_properties()

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
