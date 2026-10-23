"""V45.3: shared preview budget across an entire diagnostic report.

Author: Abdelhalim Talbi.

Tracks successful raster previews, not requests, so oversized PNGs do not
consume a slot. A single instance must be shared between source, target and
split/merge passes. The limits cover embedded PNG payloads; they are not a
CPU-time or HTML-size sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PreviewBudget:
    max_pages: int = 24
    max_png_bytes: int = 24 * 1024 * 1024
    used_pages: int = 0
    used_png_bytes: int = 0

    def __post_init__(self) -> None:
        if (type(self.max_pages) is not int or self.max_pages < 0
                or type(self.max_png_bytes) is not int or self.max_png_bytes < 0):
            raise ValueError('Preview budget limits must be non-negative integers')
        if self.used_pages != 0 or self.used_png_bytes != 0:
            raise ValueError('Preview budget counters must start at zero')

    @property
    def available(self) -> bool:
        return self.used_pages < self.max_pages and self.used_png_bytes < self.max_png_bytes

    @property
    def remaining_pages(self) -> int:
        return max(0, self.max_pages - self.used_pages)

    def reserve(self, png_bytes: int) -> bool:
        """Charge a successfully rendered preview exactly once, or reject it."""
        if type(png_bytes) is not int or png_bytes <= 0:
            raise ValueError('Preview PNG length must be a positive integer')
        if not self.available or png_bytes > self.max_png_bytes - self.used_png_bytes:
            return False
        self.used_pages += 1
        self.used_png_bytes += png_bytes
        return True
