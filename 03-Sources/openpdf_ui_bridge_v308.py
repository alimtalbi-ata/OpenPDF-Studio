"""V30.8: TaskRunner cancellation forwarded through conversion to atomic commit."""
from types import MethodType
from openpdf_ui_bridge_v301 import CONVERSION_ROUTES
from openpdf_conversion_controller_v308 import ConversionController

def connect(app):
    if getattr(app, '_v308_connected', False): return app
    original = app._run_pdf
    def routed(self, operation, *args):
        kind = CONVERSION_ROUTES.get(operation)
        if kind is None: return original(operation, *args)
        if len(args) != 2: raise ValueError('Source et destination requises')
        def worker(*, progress=None, cancelled=None):
            result = ConversionController().convert(args[0], args[1], kind, cancelled=cancelled, progress=progress)
            return str(result.destination)
        return original(worker)
    app._run_pdf = MethodType(routed, app)
    app._v308_connected = True
    return app
