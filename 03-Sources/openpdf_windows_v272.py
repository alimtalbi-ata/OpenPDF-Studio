"""V27.2 async operations wired into the existing GUI. Abdelhalim Talbi."""
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from openpdf_windows_v271 import OpenPDFStudio as BaseStudio
from openpdf_engine_v272 import merge_pdfs, extract_pages, compress_pdf

class OpenPDFStudio(BaseStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.2 — Abdelhalim Talbi')
        self._v272_busy = False
        self._v272_bar = ttk.Progressbar(self, mode='indeterminate')
        self._v272_bar.pack(side='bottom', fill='x')
        self._v272_bar.pack_forget()
        self.bind('<Control-Shift-m>', lambda _: self.merge_async())
        self.bind('<Control-Shift-c>', lambda _: self.compress_async())
        self.bind('<Control-Shift-d>', lambda _: self.extract_async())

    def _run_pdf(self, operation, *args):
        if self._v272_busy:
            messagebox.showinfo('Traitement', 'Un traitement est déjà en cours.')
            return
        self._v272_busy = True
        self._v272_bar.pack(side='bottom', fill='x')
        self._v272_bar.start(12)
        future = self.task_runner.submit(operation, *args)
        def poll():
            if not self.winfo_exists():
                return
            if not future.done():
                self.after(100, poll)
                return
            self._v272_bar.stop()
            self._v272_bar.pack_forget()
            self._v272_busy = False
            result = future.result()
            if result.error:
                messagebox.showerror('Erreur PDF', str(result.error))
            else:
                messagebox.showinfo('Terminé', f'Fichier créé : {result.value}')
        self.after(100, poll)

    def merge_async(self):
        paths = filedialog.askopenfilenames(title='PDF à fusionner', filetypes=[('PDF', '*.pdf')])
        if not paths: return
        dest = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF', '*.pdf')])
        if dest: self._run_pdf(merge_pdfs, paths, dest)

    def compress_async(self):
        path = filedialog.askopenfilename(filetypes=[('PDF', '*.pdf')])
        if not path: return
        dest = filedialog.asksaveasfilename(defaultextension='.pdf', initialfile=Path(path).stem+'-compresse.pdf')
        if dest: self._run_pdf(compress_pdf, path, dest)

    def extract_async(self):
        from tkinter import simpledialog
        path = filedialog.askopenfilename(filetypes=[('PDF', '*.pdf')])
        if not path: return
        first = simpledialog.askinteger('Découper', 'Première page (à partir de 1)', minvalue=1)
        if first is None: return
        last = simpledialog.askinteger('Découper', 'Dernière page', minvalue=first)
        if last is None: return
        dest = filedialog.asksaveasfilename(defaultextension='.pdf')
        if dest: self._run_pdf(extract_pages, path, dest, first, last)

    def _invoke_action(self, handler):
        handler = {'_merge': 'merge_async', '_compress': 'compress_async', '_split': 'extract_async'}.get(handler, handler)
        if handler in ('merge_async', 'compress_async', 'extract_async'):
            return getattr(self, handler)()
        return super()._invoke_action(handler)

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
