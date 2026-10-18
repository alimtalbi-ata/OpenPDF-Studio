"""V30.9: publication atomique, suivi de phase et erreur contextualisée."""
from pathlib import Path
from openpdf_conversion_controller_v308 import ConversionController as Previous, ConversionCancelled

class ConversionError(RuntimeError):
    """Erreur de conversion avec indication du format et de la cause."""

class ConversionController(Previous):
    def convert(self, source, destination, format=None, *, cancelled=None, progress=None, phase=None):
        ext = (format or Path(destination).suffix.lstrip('.')).lower().lstrip('.')
        def announce(stage):
            if phase is not None:
                try: phase(stage)
                except Exception: pass  # UI notification must not break conversion.
        announce('validation')
        def tracked_cancel():
            if cancelled is not None and cancelled():
                announce('annulation')
                return True
            return False
        def tracked_progress(done, total):
            announce('termine')
            if progress is not None:
                try: progress(done, total)
                except Exception: pass
        announce('conversion')
        try:
            result = super().convert(source, destination, format, cancelled=tracked_cancel, progress=tracked_progress)
        except (ConversionCancelled, ValueError):
            raise
        except Exception as exc:
            announce('erreur')
            raise ConversionError(f'Conversion {ext.upper()} impossible : {exc}') from exc
        return result
