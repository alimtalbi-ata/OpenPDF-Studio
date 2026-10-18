"""UI-independent command layer for core PDF operations. Abdelhalim Talbi.

All commands share one validation and error boundary; no Tkinter dependency.
The legacy UI is not yet rewired to this layer.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf

@dataclass(frozen=True)
class CommandResult:
    operation: str
    destination: Path
    bytes_written: int

class PDFCommands:
    def __init__(self, progress: Optional[Callable] = None, cancelled: Optional[Callable] = None):
        self.progress = progress
        self.cancelled = cancelled

    def _execute(self, name, action, destination):
        dest = Path(destination).expanduser().resolve()
        result = action()
        if not dest.is_file() or dest.stat().st_size == 0:
            raise RuntimeError(f"{name}: résultat absent ou vide")
        return CommandResult(name, dest, dest.stat().st_size)

    def merge(self, sources, destination):
        paths = list(sources)
        return self._execute('merge', lambda: merge_pdfs(paths, destination, progress=self.progress, cancelled=self.cancelled), destination)

    def extract(self, source, destination, first, last):
        return self._execute('extract', lambda: extract_pages(source, destination, first, last, progress=self.progress, cancelled=self.cancelled), destination)

    def compress(self, source, destination):
        return self._execute('compress', lambda: compress_pdf(source, destination, progress=self.progress, cancelled=self.cancelled), destination)
