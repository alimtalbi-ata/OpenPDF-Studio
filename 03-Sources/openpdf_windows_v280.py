"""V28.0: coordinated polling and shutdown, incremental UI refactor.
Author: Abdelhalim Talbi.
"""
from openpdf_windows_v279 import OpenPDFStudio as PreviousStudio
from openpdf_ui_controller_v280 import UIController

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        self._v280_controller = None
        super().__init__()
        self.title('OpenPDF Studio V28.0 — Abdelhalim Talbi')
        self._v280_controller = UIController(self.after, self.after_cancel)

    def _poll_v274(self):
        # The inherited polling implementation calls self.after directly;
        # the V28.0 controller owns the newly initiated polling cycle.
        return super()._poll_v274()

    def _close_v274(self):
        if self._task_state.busy:
            return super()._close_v274()
        if self._v280_controller is not None:
            self._v280_controller.close()
        return super()._close_v274()

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
