"""V27.6 centralized commands and one toolbar. Abdelhalim Talbi."""
from tkinter import ttk, messagebox
from openpdf_windows_v275 import OpenPDFStudio as PreviousStudio
from openpdf_commands_v276 import COMMANDS, CommandRouter

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.6 — Abdelhalim Talbi')
        self.command_router = CommandRouter(self, lambda: self._task_state.busy)
        self._install_v276_toolbar()

    def _install_v276_toolbar(self):
        # Remove the V27.0 declarative toolbar, retaining document navigator and panes.
        for child in list(self.winfo_children()):
            if not isinstance(child, ttk.Frame) or child is self.main_panes:
                continue
            texts = {w.cget('text') for w in child.winfo_children() if isinstance(w, ttk.Button)}
            if {'Ajouter', 'Fusionner', 'Compresser', 'Découper'}.issubset(texts):
                child.destroy()
        bar = ttk.Frame(self, padding=(12, 6))
        bar.pack(fill='x', before=self.main_panes)
        for cmd in COMMANDS:
            ttk.Button(bar, text=cmd.label, command=lambda key=cmd.key: self._run_command_v276(key)).pack(side='left', padx=(0, 6))
        self.bind('<Control-o>', lambda event: self._run_command_v276('add'))
        self.bind('<Control-s>', lambda event: self._run_command_v276('save'))

    def _run_command_v276(self, key):
        try:
            if not self.command_router.dispatch(key):
                self._v273_label.configure(text='Traitement en cours : commande indisponible')
        except Exception as exc:
            self._diagnostics.exception('Command execution failed: %s', key)
            messagebox.showerror('Erreur', 'Commande indisponible. Consultez le journal de diagnostic.')

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
