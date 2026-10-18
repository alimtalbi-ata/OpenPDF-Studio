"""OpenPDF Studio V26.3: visual thumbnail gallery and drag reorder. Author: Abdelhalim Talbi."""
import base64
import tkinter as tk
from tkinter import ttk, messagebox
from openpdf_windows_v262 import PageEditor as BasePageEditor, OpenPDFStudio as BaseStudio
from openpdf_core_v261 import preview_png


def reorder_pages(pages, indices, target):
    """Insert selected pages before target (target is original zero-based slot)."""
    indices = sorted(set(indices))
    if not indices or any(not 0 <= i < len(pages) for i in indices):
        return list(pages), []
    if not isinstance(target, int) or not 0 <= target <= len(pages):
        raise ValueError('Position de destination invalide')
    selected = [pages[i] for i in indices]
    remaining = [p for i, p in enumerate(pages) if i not in indices]
    insert_at = target - sum(i < target for i in indices)
    result = remaining[:insert_at] + selected + remaining[insert_at:]
    return result, list(range(insert_at, insert_at + len(selected)))


class PageEditor(BasePageEditor):
    def _build(self):
        super()._build()
        # Gallery is a secondary pane: the original list, commands and PDF preview remain available.
        self.gallery_frame = ttk.LabelFrame(self, text='Miniatures des pages — glisser pour réordonner', padding=6)
        self.gallery_frame.pack(fill='x', padx=12, pady=(0, 12))
        self.gallery_canvas = tk.Canvas(self.gallery_frame, height=172, bg='#edf2f8', highlightthickness=0)
        scroll = ttk.Scrollbar(self.gallery_frame, orient='horizontal', command=self.gallery_canvas.xview)
        self.gallery_canvas.configure(xscrollcommand=scroll.set)
        self.gallery_canvas.pack(fill='x', expand=True)
        scroll.pack(fill='x')
        self._thumb_cache = {}
        self._thumb_refs = []
        self._drag_start = None
        self.gallery_canvas.bind('<ButtonPress-1>', self._drag_begin)
        self.gallery_canvas.bind('<ButtonRelease-1>', self._drag_end)
        self.gallery_canvas.bind('<Configure>', lambda e: self._render_gallery())
        self.bind('<Control-a>', lambda e: self.listbox.selection_set(0, 'end'))

    def _redraw(self, selected=None):
        super()._redraw(selected)
        if hasattr(self, 'gallery_canvas'):
            self._render_gallery()

    def _render_gallery(self):
        canvas = self.gallery_canvas
        canvas.delete('all')
        self._thumb_refs = []
        selected = set(self.listbox.curselection())
        for i, page in enumerate(self.pages):
            x = 8 + i * 116
            canvas.create_rectangle(x, 5, x + 106, 153, fill='#d6e9ff' if i in selected else 'white', outline='#3b82f6' if i in selected else '#aeb8c7', width=2 if i in selected else 1, tags=(f'page-{i}',))
            key = page['number']
            if key not in self._thumb_cache:
                try:
                    png = preview_png(self.source, key, 94, 120)
                    self._thumb_cache[key] = tk.PhotoImage(data=base64.b64encode(png).decode('ascii'))
                except Exception:
                    self._thumb_cache[key] = None
            photo = self._thumb_cache[key]
            if photo:
                self._thumb_refs.append(photo)
                canvas.create_image(x + 53, 65, image=photo, tags=(f'page-{i}',))
            else:
                canvas.create_text(x + 53, 65, text='Aperçu indisponible', width=90, tags=(f'page-{i}',))
            canvas.create_text(x + 53, 139, text=f'{i+1} · p.{key} ↻{page["rotation"]}°', font=('Segoe UI', 8), tags=(f'page-{i}',))
        canvas.configure(scrollregion=(0, 0, max(1, 16 + len(self.pages) * 116), 160))

    def _gallery_index(self, event):
        return int(self.gallery_canvas.canvasx(event.x) // 116)

    def _drag_begin(self, event):
        index = self._gallery_index(event)
        if not 0 <= index < len(self.pages):
            self._drag_start = None
            return
        chosen = list(self.listbox.curselection())
        if index not in chosen:
            self.listbox.selection_clear(0, 'end')
            self.listbox.selection_set(index)
            self._selection_changed()
            chosen = [index]
        self._drag_start = chosen

    def _drag_end(self, event):
        chosen = self._drag_start
        self._drag_start = None
        if not chosen:
            return
        target = max(0, min(len(self.pages), self._gallery_index(event)))
        self.pages, new_indices = reorder_pages(self.pages, chosen, target)
        self._redraw(new_indices)

    def _selection_changed(self, event=None):
        super()._selection_changed(event)
        if hasattr(self, 'gallery_canvas'):
            self._render_gallery()


class OpenPDFStudio(BaseStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V26.3 — Abdelhalim Talbi')

    def open_preview(self):
        if self.busy:
            return
        if not self.files:
            messagebox.showwarning('Aucun PDF', 'Ajoutez un PDF avant de modifier ses pages.')
            return
        selection = self.filelist.curselection()
        source = self.files[selection[0]] if selection else self.files[0]
        try:
            PageEditor(self, source)
        except Exception as exc:
            messagebox.showerror('Éditeur de pages', str(exc))


if __name__ == '__main__':
    OpenPDFStudio().mainloop()
