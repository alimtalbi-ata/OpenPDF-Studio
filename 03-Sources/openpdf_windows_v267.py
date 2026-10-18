"""OpenPDF Studio V26.7 — responsive workspace. Author: Abdelhalim Talbi."""
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from openpdf_windows_v266 import OpenPDFStudio as PreviousStudio
from openpdf_windows_v265 import describe_document

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V26.7 — Abdelhalim Talbi')
        self._properties_generation = 0
        self._create_quick_toolbar()

    def _create_quick_toolbar(self):
        """One compact entry point for frequent actions; no extra windows."""
        bar = ttk.Frame(self, padding=(14, 4))
        # Put the toolbar directly below the heading, before the main panes.
        bar.pack(fill='x', before=self.main_panes)
        for title, callback in (
            ('+ Ajouter', self.add_files),
            ('Éditer les pages', self.open_preview),
            ('Enregistrer les pages', self._save_editor),
            ('Fusionner', lambda: self._choose_operation('Fusionner des PDF')),
            ('Compresser', lambda: self._choose_operation('Compresser / optimiser')),
            ('Découper', lambda: self._choose_operation('Découper en pages')),
        ):
            ttk.Button(bar, text=title, command=callback).pack(side='left', padx=(0, 6))

    def _choose_operation(self, operation):
        self.operation.set(operation)
        self._refresh()
        self.status.set('Opération sélectionnée : ' + operation)

    def _save_editor(self):
        if getattr(self.editor, 'source', None):
            self.editor.save()
        else:
            self.status.set('Ouvrez un PDF dans l’éditeur avant d’enregistrer.')

    def _update_properties(self, event=None):
        """Inspect PDF metadata off the Tk event loop; discard obsolete results."""
        if not getattr(self, 'files', None):
            return
        selected = self.filelist.curselection()
        source = self.files[selected[0]] if selected else self.files[0]
        self._properties_generation += 1
        generation = self._properties_generation
        self._set_properties('Analyse du document en cours…')

        def inspect():
            try:
                data = describe_document(source)
                result = ('Document : {name}\nPages : {pages}\nTaille : {size_bytes:,} octets\n'
                          'Première page : {width} × {height} pt\n').format(**data)
            except Exception as exc:
                result = 'Propriétés indisponibles : ' + str(exc)
            # Only the main thread may touch widgets.
            try:
                self.after(0, lambda: self._deliver_properties(generation, result))
            except RuntimeError:
                pass
        threading.Thread(target=inspect, daemon=True).start()

    def _deliver_properties(self, generation, result):
        if generation == self._properties_generation and self.winfo_exists():
            self._set_properties(result)

    def _set_properties(self, result):
        self.properties_text.configure(state='normal')
        self.properties_text.delete('1.0', 'end')
        self.properties_text.insert('1.0', result)
        self.properties_text.configure(state='disabled')

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
