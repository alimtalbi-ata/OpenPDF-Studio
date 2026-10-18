"""V30.9: conversion routée et annulation coopérative avec phase observable."""
from types import MethodType
from openpdf_ui_bridge_v301 import CONVERSION_ROUTES
from openpdf_conversion_controller_v309 import ConversionController

def connect(app):
    if getattr(app, '_v309_connected', False): return app
    original = app._run_pdf
    def routed(self, operation, *args):
        kind = CONVERSION_ROUTES.get(operation)
        if kind is None: return original(operation, *args)
        if len(args) != 2: raise ValueError('Source et destination requises')
        def worker(*, progress=None, cancelled=None):
            def phase(stage):
                # Optional observer: do not update Tk widgets from a worker thread.
                observer = getattr(self, '_conversion_phase_observer', None)
                if observer is not None: observer(stage)
            result = ConversionController().convert(args[0], args[1], kind, cancelled=cancelled, progress=progress, phase=phase)
            return str(result.destination)
        return original(worker)
    app._run_pdf = MethodType(routed, app)
    app._v309_connected = True
    return app
