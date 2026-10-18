"""V27.7: single command toolbar, contextual status and UI state. Abdelhalim Talbi."""
from tkinter import ttk, messagebox
from openpdf_windows_v276 import OpenPDFStudio as PreviousStudio
from openpdf_commands_v276 import COMMANDS
from openpdf_ui_layout_v277 import unique_commands, normalize_progress

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.7 — Abdelhalim Talbi')
        self._command_buttons = {}
        self._replace_command_toolbar()
        self._refresh_command_states()

    def _replace_command_toolbar(self):
        # Only remove known command bars. Do not delete the navigator, panes or status.
        labels = {item.label for item in COMMANDS}
        for child in list(self.winfo_children()):
            if child is self.main_panes or not isinstance(child, ttk.Frame):
                continue
            button_labels = {w.cget('text') for w in child.winfo_children() if isinstance(w, ttk.Button)}
            if {'Ajouter', 'Fusionner', 'Compresser', 'Découper'}.issubset(button_labels) and button_labels.issubset(labels | {'Enregistrer les pages', 'Éditer les pages'}):
                child.destroy()
        bar = ttk.Frame(self, padding=(12, 7))
        bar.pack(fill='x', before=self.main_panes)
        for command in unique_commands(COMMANDS):
            btn = ttk.Button(bar, text=command.label, command=lambda key=command.key: self._run_command_v276(key))
            btn.pack(side='left', padx=(0, 7))
            self._command_buttons[command.key] = btn
        self._v277_toolbar = bar

    def _refresh_command_states(self):
        if not self.winfo_exists():
            return
        busy = self._task_state.busy
        for command in COMMANDS:
            self._command_buttons[command.key].configure(state='disabled' if busy and command.requires_idle else 'normal')
        self.after(180, self._refresh_command_states)

    def _poll_v274(self):
        if self._v273_handle is not None:
            self._v273_progress.configure(value=normalize_progress(self._v273_handle.progress))
        super()._poll_v274()

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
