"""Preserve user-authored PDF document properties during page extraction/reorder.

Only standard descriptive fields are copied. Producer, modification timestamps,
custom XMP and signatures are deliberately NOT claimed as preserved.
Fail closed before publication if metadata cannot be reproduced exactly.
Author: Abdelhalim Talbi. OpenPDF Studio V50.1.
"""
from __future__ import annotations

from dataclasses import dataclass

FIELDS = ("title", "author", "subject", "keywords", "creator")
MAX_FIELD_UTF8_BYTES = 262_144


@dataclass(frozen=True)
class MetadataPlan:
    fields: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, str]:
        return dict(self.fields)


def prepare_metadata(document) -> MetadataPlan:
    """Read a PyMuPDF source document and validate descriptive metadata."""
    if document.needs_pass:
        raise ValueError("PDF protégé : métadonnées indisponibles")
    metadata = document.metadata or {}
    values = []
    for key in FIELDS:
        value = metadata.get(key) or ""
        if not isinstance(value, str):
            raise ValueError(f"Métadonnée invalide : {key}")
        if "\x00" in value or len(value.encode("utf-8")) > MAX_FIELD_UTF8_BYTES:
            raise ValueError(f"Métadonnée dangereuse ou trop volumineuse : {key}")
        values.append((key, value))
    return MetadataPlan(tuple(values))


def apply_metadata(document, plan: MetadataPlan) -> None:
    if not isinstance(plan, MetadataPlan):
        raise TypeError("Plan de métadonnées invalide")
    document.set_metadata(plan.as_dict())


def verify_metadata(document, plan: MetadataPlan) -> None:
    if not isinstance(plan, MetadataPlan):
        raise TypeError("Plan de métadonnées invalide")
    observed = document.metadata or {}
    for key, expected in plan.fields:
        if observed.get(key, "") != expected:
            raise RuntimeError(f"Fidélité des métadonnées non respectée : {key}")
