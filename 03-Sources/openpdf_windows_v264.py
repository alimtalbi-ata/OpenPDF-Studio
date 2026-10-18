"""OpenPDF Studio V26.4: virtualized gallery and zoom. Author: Abdelhalim Talbi."""
import base64
import tkinter as tk
from tkinter import ttk, messagebox
from openpdf_windows_v263 import PageEditor as PreviousEditor, OpenPDFStudio as PreviousStudio
from openpdf_core_v261 import preview_png

CELL_WIDTH = 116

def visible_range(offset, viewport, count, cell_width=CELL_WIDTH, overscan=2):
    """Visible page indices, with overscan for smooth scrolling."""
    if count <= 0: return range(0)
    if viewport <= 0: return range(0)
    start = max(0, int(max(0, offset) // cell_width) - overscan)
    end = min(count, int((max(0, offset) + viewport) // cell_width) + overscan + 1)
    return range(start, end)

class PageEditor(PreviousEditor):
    def _build(self):
        super()._build()
        self.zoom_factor = tk.DoubleVar(value=1.0)
        controls = ttk.Frame(self.gallery_frame)
        controls.pack(fill='x', before=self.gallery_canvas)
        ttk.Label(controls, text='Zoom aperçu :').pack(side='left')
        for label, factor in [('−', .75), ('100 %', 1.0), ('+', 1.25)]:
            ttk.Button(controls, text=label, width=6, command=lambda f=factor: self.change_zoom(f)).pack(side='left', padx=2)
        self.zoom_label = ttk.Label(controls, text='100 %')
        self.zoom_label.pack(side='left', padx=8)
        self._gallery_scrollbar = next(w for w in self.gallery_frame.winfo_children() if isinstance(w, ttk.Scrollbar))
        self.gallery_canvas.configure(xscrollcommand=self._scrollbar_set)
        self.gallery_canvas.bind('<MouseWheel>', self._wheel_scroll)
        self.gallery_canvas.bind('<Button-4>', lambda e: self._wheel_scroll_linux(-1))
        self.gallery_canvas.bind('<Button-5>', lambda e: self._wheel_scroll_linux(1))

    def change_zoom(self, multiplier):
        value = 1.0 if multiplier == 1.0 else max(.5, min(2.0, round(self.zoom_factor.get() * multiplier, 2)))
        self.zoom_factor.set(value)
        self.zoom_label.configure(text=f'{value * 100:.0f} %')
        self._selection_changed()

    def _selection_changed(self, event=None):
        # Preserve base selection/summary; rerender the preview at the requested size.
        super()._selection_changed(event)
        if not hasattr(self, 'zoom_factor'): return
        selection = self.listbox.curselection()
        if not selection: return
        page = self.pages[selection[0]]
        try:
            factor = self.zoom_factor.get()
            png = preview_png(self.source, page['number'], min(2048, int(550*factor)), min(2048, int(610*factor)))
            photo = tk.PhotoImage(data=base64.b64encode(png).decode('ascii'))
            self.preview.configure(image=photo, text='')
            self.preview.image = photo
        except Exception as exc:
            self.preview.configure(image='', text=str(exc))
            self.preview.image = None

    def _scrollbar_set(self, first, last):
        # Called on viewport changes and horizontal scrolls.
        self._gallery_scrollbar.set(first, last)
        if hasattr(self, '_thumb_cache'):
            position = (first, last)
            if position != getattr(self, '_last_scroll_position', None):
                self._last_scroll_position = position
                if not getattr(self, '_redraw_pending', False):
                    self._redraw_pending = True
                    self.after_idle(self._deferred_gallery)

    def _deferred_gallery(self):
        self._redraw_pending = False
        self._render_gallery()

    def _wheel_scroll(self, event):
        self.gallery_canvas.xview_scroll(-1 if event.delta > 0 else 1, 'units')
        return 'break'

    def _wheel_scroll_linux(self, direction):
        self.gallery_canvas.xview_scroll(direction, 'units')
        return 'break'

    def _render_gallery(self):
        canvas = self.gallery_canvas
        if not hasattr(canvas, 'winfo_width'): return
        canvas.delete('all')
        count = len(self.pages)
        canvas.configure(scrollregion=(0, 0, max(1, 16 + count*CELL_WIDTH), 160))
        viewport = canvas.winfo_width()
        offset = canvas.canvasx(0)
        selected = set(self.listbox.curselection())
        self._thumb_refs = []
        for i in visible_range(offset, viewport, count):
            page = self.pages[i]
            x = 8 + i*CELL_WIDTH
            canvas.create_rectangle(x, 5, x+106, 153, fill='#d6e9ff' if i in selected else 'white', outline='#3b82f6' if i in selected else '#aeb8c7', width=2 if i in selected else 1)
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
                canvas.create_image(x+53, 65, image=photo)
            else:
                canvas.create_text(x+53, 65, text='Aperçu indisponible', width=90)
            canvas.create_text(x+53, 139, text=f'{i+1} · p.{key} ↻{page["rotation"]}°', font=('Segoe UI', 8))
        # Bound the image cache for large PDFs; pages outside the viewport can be rerendered.
        keep = {self.pages[i]['number'] for i in visible_range(offset, viewport, count, overscan=8)}
        for key in list(self._thumb_cache):
            if key not in keep: del self._thumb_cache[key]

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V26.4 — Abdelhalim Talbi')
    def open_preview(self):
        if self.busy: return
        if not self.files:
            messagebox.showwarning('Aucun PDF', 'Ajoutez un PDF avant de modifier ses pages.')
            return
        selection = self.filelist.curselection()
        source = self.files[selection[0]] if selection else self.files[0]
        try: PageEditor(self, source)
        except Exception as exc: messagebox.showerror('Éditeur de pages', str(exc))

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
