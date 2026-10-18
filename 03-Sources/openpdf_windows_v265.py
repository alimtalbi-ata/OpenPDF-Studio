"""OpenPDF Studio V26.5 — unified desktop workspace. Author: Abdelhalim Talbi."""
import base64
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from openpdf_windows_v264 import OpenPDFStudio as PreviousStudio
from openpdf_windows_v262 import PageEditor as PreviousEditor
from openpdf_core_v261 import page_info, preview_png, edit_pages


def describe_document(source):
    """Pure-ish document summary, reusable in CLI/tests and the properties panel."""
    pages = page_info(source)
    if not pages:
        raise ValueError('Document PDF vide')
    return {'name': Path(source).name, 'pages': len(pages),
            'size_bytes': Path(source).stat().st_size,
            'width': pages[0]['width'], 'height': pages[0]['height']}


class EmbeddedEditor(ttk.Frame):
    """Page editor embedded in the main workspace, without a Toplevel."""
    _redraw = PreviousEditor._redraw
    _selection_changed = PreviousEditor._selection_changed
    move = PreviousEditor.move
    rotate = PreviousEditor.rotate
    delete = PreviousEditor.delete

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.source = None
        self.pages = []
        self.selected = tk.IntVar(value=0)
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', pady=(0, 8))
        for label, cmd in [('↑ Monter', lambda: self.move(-1)),
                           ('↓ Descendre', lambda: self.move(1)),
                           ('↻ +90°', lambda: self.rotate(90)),
                           ('↺ -90°', lambda: self.rotate(-90)),
                           ('Supprimer', self.delete),
                           ('Enregistrer sous…', self.save)]:
            ttk.Button(toolbar, text=label, command=cmd).pack(side='left', padx=3)
        pane = ttk.Panedwindow(self, orient='horizontal')
        pane.pack(fill='both', expand=True)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=1)
        pane.add(right, weight=3)
        ttk.Label(left, text='Pages — Ctrl/Maj pour sélectionner').pack(anchor='w')
        self.listbox = tk.Listbox(left, selectmode='extended', exportselection=False,
                                  bg='#1b2c46', fg='#eaf3ff', selectbackground='#3b79b7',
                                  font=('Segoe UI', 10))
        self.listbox.pack(fill='both', expand=True, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self._selection_changed)
        self.summary = ttk.Label(right, text='Ouvrez un PDF dans l’explorateur.')
        self.summary.pack(anchor='w')
        self.preview = tk.Label(right, bg='#26374d', fg='white', text='Aucun PDF sélectionné')
        self.preview.pack(fill='both', expand=True, pady=6)

    def load(self, source):
        info = page_info(source)
        self.source = str(source)
        self.pages = [{'number': p['number'], 'rotation': p['rotation']} for p in info]
        self.selected.set(0)
        self._redraw()

    def _selection_changed(self, event=None):
        if not self.source:
            self.summary.configure(text='Aucun PDF ouvert')
            return
        PreviousEditor._selection_changed(self, event)

    def save(self):
        if not self.source or not self.pages:
            messagebox.showwarning('Aucun PDF', 'Ouvrez un PDF avant d’enregistrer.', parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title='Enregistrer le PDF modifié',
                                            defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if not path: return
        if Path(path).exists() and not messagebox.askyesno('Confirmation', 'Remplacer le PDF existant ?', parent=self): return
        try:
            edit_pages(self.source, path, [p['number'] for p in self.pages],
                       {p['number']: p['rotation'] for p in self.pages})
        except Exception as exc:
            messagebox.showerror('Erreur', str(exc), parent=self)
            return
        messagebox.showinfo('Enregistrement', 'PDF enregistré : ' + path, parent=self)


class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V26.5 — Abdelhalim Talbi')
        self.geometry('1200x800')
        self.minsize(900, 600)
        self._create_workspace()

    def _create_workspace(self):
        # Preserve the existing PDF operations in a dedicated tab, and provide
        # an embedded editor in the same top-level window.
        self.workspace = ttk.Notebook(self)
        self.workspace.pack(fill='both', expand=True, padx=14, pady=(0, 12))
        self.editor = EmbeddedEditor(self.workspace)
        self.workspace.add(self.editor, text='  Éditeur de pages  ')
        self.properties = ttk.Frame(self.workspace, padding=18)
        self.workspace.add(self.properties, text='  Propriétés du PDF  ')
        self.properties_text = tk.Text(self.properties, height=15, bg='#1b2c46', fg='#eaf3ff',
                                       font=('Consolas', 11), relief='flat', state='disabled')
        self.properties_text.pack(fill='both', expand=True)
        # Reuse the existing operations and file explorer, without additional portals.
        self.filelist.bind('<Double-Button-1>', lambda event: self.open_preview())
        self.filelist.bind('<<ListboxSelect>>', self._update_properties)

    def _update_properties(self, event=None):
        if not self.files: return
        selected = self.filelist.curselection()
        source = self.files[selected[0]] if selected else self.files[0]
        try:
            data = describe_document(source)
            content = ('Document : {name}\nPages : {pages}\nTaille : {size_bytes:,} octets\n'
                       'Première page : {width} × {height} pt\n').format(**data)
        except Exception as exc:
            content = 'Propriétés indisponibles : ' + str(exc)
        self.properties_text.configure(state='normal')
        self.properties_text.delete('1.0', 'end')
        self.properties_text.insert('1.0', content)
        self.properties_text.configure(state='disabled')

    def open_preview(self):
        if self.busy: return
        if not self.files:
            messagebox.showwarning('Aucun PDF', 'Ajoutez un PDF pour accéder à l’éditeur.')
            return
        selected = self.filelist.curselection()
        source = self.files[selected[0]] if selected else self.files[0]
        try:
            self.editor.load(source)
            self.workspace.select(self.editor)
            self._update_properties()
        except Exception as exc:
            messagebox.showerror('Éditeur', str(exc))

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
