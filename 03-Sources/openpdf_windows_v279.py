"""V27.9: one lifecycle-managed command refresh timer. Abdelhalim Talbi."""
from openpdf_windows_v278 import OpenPDFStudio as PreviousStudio
from openpdf_commands_v276 import COMMANDS
from openpdf_ui_shell_v278 import command_enabled
from openpdf_ui_lifecycle_v279 import RefreshScheduler

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        # Base constructors schedule a legacy refresh. Override the method
        # before super().__init__ so no duplicate refresh loop is started.
        self._v279_refresh = None
        super().__init__()
        self.title('OpenPDF Studio V27.9 — Abdelhalim Talbi')
        self._v279_refresh = RefreshScheduler(self.after, self.after_cancel)
        self._v279_refresh.start(self._update_command_states)

    def _refresh_command_states(self):
        # Called during V27.7 initialization: V27.9 owns the only timer.
        if self._v279_refresh is not None:
            self._update_command_states()

    def _update_command_states(self):
        if not self.winfo_exists():
            return
        busy = self._task_state.busy
        for command in COMMANDS:
            button = self._command_buttons.get(command.key)
            if button is not None and button.winfo_exists():
                button.configure(state='normal' if command_enabled(command, busy) else 'disabled')

    def _close_v274(self):
        if self._task_state.busy:
            return super()._close_v274()
        if self._v279_refresh is not None:
            self._v279_refresh.close()
        return super()._close_v274()

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
