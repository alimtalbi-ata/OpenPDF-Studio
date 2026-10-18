"""OpenPDF Studio V26.9: single-explorer workspace adaptation.

Author: Abdelhalim Talbi. Preserves the proven PDF processing API.
"""
import tkinter as tk
from tkinter import ttk
from openpdf_windows_v267 import OpenPDFStudio as LegacyStudio

class OpenPDFStudio(LegacyStudio):
    """Single document navigator with keyboard-first commands."""
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V26.9 — Abdelhalim Talbi')
        self.geometry('1120x760')
        self.minsize(860, 580)
        # Keep the original list as an internal compatibility adapter. Existing
        # editing and processing methods still refer to its selection indices.
        self.filelist.pack_forget()
        self.sidebar_files.configure(font=('Segoe UI', 11), activestyle='dotbox')
        self.bind('<Control-o>', lambda _event: self.add_files())
        self.bind('<Control-s>', lambda _event: self._save_editor())
        self.bind('<Control-Return>', lambda _event: self.run() if not self.busy else None)
        self.bind('<F5>', lambda _event: self._update_properties())
        self._install_accessible_actions()

    def _install_accessible_actions(self):
        actions = ttk.Frame(self.sidebar, padding=(0, 8))
        actions.pack(fill='x')
        ttk.Button(actions, text='Ajouter', command=self.add_files).pack(side='left', expand=True, fill='x')
        ttk.Button(actions, text='Retirer tout', command=self.clear_files).pack(side='left', expand=True, fill='x', padx=(6, 0))
        ttk.Label(self.sidebar, text='Double-clic : ouvrir les pages\nCtrl+O : ajouter · Ctrl+S : enregistrer',
                  wraplength=240).pack(anchor='w', pady=(6, 0))

if __name__ == '__main__':
    app = OpenPDFStudio()
    app.mainloop()
