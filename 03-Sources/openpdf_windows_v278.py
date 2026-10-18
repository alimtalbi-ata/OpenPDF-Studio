"""V27.8: single owned command bar and declarative keyboard bindings. Abdelhalim Talbi."""
from tkinter import ttk
from openpdf_windows_v277 import OpenPDFStudio as PreviousStudio
from openpdf_commands_v276 import COMMANDS
from openpdf_ui_shell_v278 import SHORTCUTS, validate_shortcuts, command_enabled

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.8 — Abdelhalim Talbi')
        self._remove_duplicate_command_bars()
        self._install_shortcuts_v278()

    def _remove_duplicate_command_bars(self):
        # V27.6 created an untracked toolbar; retain only the owned V27.7 bar.
        expected = {cmd.label for cmd in COMMANDS}
        for child in list(self.winfo_children()):
            if child is self._v277_toolbar or not isinstance(child, ttk.Frame):
                continue
            labels = {w.cget('text') for w in child.winfo_children() if isinstance(w, ttk.Button)}
            if {'Ajouter', 'Fusionner', 'Compresser', 'Découper'}.issubset(labels) and labels.issubset(expected):
                child.destroy()

    def _install_shortcuts_v278(self):
        for shortcut in validate_shortcuts(SHORTCUTS, {cmd.key for cmd in COMMANDS}):
            self.bind(shortcut.sequence, lambda event, key=shortcut.command: self._run_command_v276(key))

    def _refresh_command_states(self):
        if not self.winfo_exists():
            return
        busy = self._task_state.busy
        for cmd in COMMANDS:
            self._command_buttons[cmd.key].configure(state='normal' if command_enabled(cmd, busy) else 'disabled')
        self.after(180, self._refresh_command_states)

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
