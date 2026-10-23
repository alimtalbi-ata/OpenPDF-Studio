"""Validated 1-based page order grammar for PDF reorganisation.

Examples: 3-1,5,5,2-4, impaires, paires, toutes, inverse. Reversed
ranges, intentional duplicates and page-set shortcuts are supported. Invalid
or oversized requests fail before PDF publication. V49.8 shortcuts.
Author: Abdelhalim Talbi. OpenPDF Studio V49.7.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

MAX_EXPRESSION_CHARS = 4096
MAX_SEGMENTS = 2048
MAX_OUTPUT_PAGES = 10000
_SEGMENT = re.compile(r"([0-9]+)(?:\s*-\s*([0-9]+))?\Z", re.ASCII)
_PAGE_SETS = {
    "toutes": "all", "all": "all",
    "impaires": "odd", "odd": "odd",
    "paires": "even", "even": "even",
    "inverse": "reverse", "reverse": "reverse",
    "premiere": "first", "première": "first", "first": "first",
    "derniere": "last", "dernière": "last", "last": "last",
}


@dataclass(frozen=True)
class PageOrderPlan:
    pages: tuple[int, ...]
    source_pages: int
    output_pages: int
    duplicated_pages: int
    omitted_pages: int


def plan_page_order(expression: str, page_count: int, *, max_output_pages: int = MAX_OUTPUT_PAGES) -> PageOrderPlan:
    if type(page_count) is not int or page_count < 1:
        raise ValueError("Nombre de pages source invalide")
    if type(max_output_pages) is not int or max_output_pages < 1:
        raise ValueError("Limite de pages de sortie invalide")
    if not isinstance(expression, str) or not expression.strip() or len(expression) > MAX_EXPRESSION_CHARS:
        raise ValueError("Ordre des pages vide ou trop long")
    segments = re.split(r"[,;]", expression)
    if len(segments) > MAX_SEGMENTS:
        raise ValueError("Trop de segments dans l'ordre des pages")
    pages: list[int] = []
    for part in segments:
        token = part.strip()
        keyword = _PAGE_SETS.get(token.casefold())
        if keyword:
            selected = {
                "all": range(1, page_count + 1),
                "odd": range(1, page_count + 1, 2),
                "even": range(2, page_count + 1, 2),
                "reverse": range(page_count, 0, -1),
                "first": range(1, 2),
                "last": range(page_count, page_count + 1),
            }[keyword]
            if not selected:
                raise ValueError(f"Aucune page pour le sélecteur : {token!r}")
            if len(pages) + len(selected) > max_output_pages:
                raise ValueError(f"Ordre trop volumineux : maximum {max_output_pages} pages")
            pages.extend(selected)
            continue
        match = _SEGMENT.fullmatch(token)
        if not match:
            raise ValueError(f"Segment de pages invalide : {token[:80]!r}")
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) is not None else first
        if first < 1 or last < 1 or first > page_count or last > page_count:
            raise ValueError(f"Page hors limites (1 à {page_count}) : {token[:80]!r}")
        count = abs(last - first) + 1
        if len(pages) + count > max_output_pages:
            raise ValueError(f"Ordre trop volumineux : maximum {max_output_pages} pages")
        step = 1 if last >= first else -1
        pages.extend(range(first, last + step, step))
    unique = len(set(pages))
    return PageOrderPlan(tuple(pages), page_count, len(pages), len(pages) - unique, page_count - unique)


def parse_page_order(expression: str, page_count: int, *, max_output_pages: int = MAX_OUTPUT_PAGES) -> list[int]:
    return list(plan_page_order(expression, page_count, max_output_pages=max_output_pages).pages)
