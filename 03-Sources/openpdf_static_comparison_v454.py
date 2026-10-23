"""V45.4: bounded, evidence-led offline navigation for PDF split/merge candidates.

Author: Abdelhalim Talbi.

No JavaScript, inferred page pairing, duplicated image payloads, or fidelity
certification. Candidate pages are rendered once in the report's shared budget;
this module only links to those real previews.
"""
from __future__ import annotations

from dataclasses import dataclass
import html
import math

MAX_CANDIDATES = 100
MAX_PAGE = 1000
MAX_PAGES_PER_SIDE = 12


@dataclass(frozen=True)
class PageCandidate:
    kind: str
    source_pages: tuple[int, ...]
    target_pages: tuple[int, ...]
    text_overlap: float


def extract_candidates(report: dict) -> tuple[PageCandidate, ...]:
    """Accept only explicit, finite, 1:2 or 2:1 text-overlap candidates."""
    if not isinstance(report, dict):
        raise ValueError('Diagnostic report must be an object')
    audit = report.get('multipage_audit')
    if not isinstance(audit, dict):
        return ()
    raw = audit.get('split_merge_candidates')
    if not isinstance(raw, list):
        return ()
    accepted: list[PageCandidate] = []
    seen: set[tuple] = set()
    for entry in raw[:MAX_CANDIDATES]:
        if not isinstance(entry, dict):
            continue
        kind = entry.get('type')
        expected = {'split': (1, 2), 'merge': (2, 1)}.get(kind) if isinstance(kind, str) else None
        if expected is None:
            continue
        source, target = entry.get('source_pages'), entry.get('target_pages')
        if not isinstance(source, list) or not isinstance(target, list):
            continue
        if (len(source), len(target)) != expected:
            continue
        pages = source + target
        if any(type(n) is not int or not 1 <= n <= MAX_PAGE for n in pages):
            continue
        if len(set(source)) != len(source) or len(set(target)) != len(target):
            continue
        overlap = entry.get('text_overlap')
        if type(overlap) not in (int, float) or not math.isfinite(overlap) or not 0 <= overlap <= 1:
            continue
        key = (kind, tuple(source), tuple(target))
        if key in seen:
            continue
        seen.add(key)
        accepted.append(PageCandidate(kind, tuple(source), tuple(target), float(overlap)))
    return tuple(accepted)


def missing_candidate_pages(candidates: tuple[PageCandidate, ...],
                            previews: dict[str, dict[int, str]], *,
                            per_side_limit: int = MAX_PAGES_PER_SIDE) -> dict[str, tuple[int, ...]]:
    """Return only not-yet-rendered candidate pages, capped per side.

    Pages already rendered for findings are reused rather than rasterized twice.
    The caller must additionally enforce its shared page/PNG byte budget.
    """
    if type(per_side_limit) is not int or per_side_limit < 0:
        raise ValueError('per_side_limit must be a non-negative integer')
    result = {}
    for side in ('source', 'target'):
        existing = set(previews.get(side, {}))
        capacity = max(0, per_side_limit - len(existing))
        requested = set()
        for candidate in candidates:
            requested.update(candidate.source_pages if side == 'source' else candidate.target_pages)
        result[side] = tuple(sorted(requested - existing)[:capacity])
    return result


def render_candidate_navigation(candidates: tuple[PageCandidate, ...],
                                previews: dict[str, dict[int, str]]) -> str:
    """Create a static, navigable 1:2/2:1 comparison without re-embedding PNGs."""
    if not candidates:
        return ''
    sections = []
    for index, candidate in enumerate(candidates, 1):
        cards = []
        for side, pages in (('source', candidate.source_pages), ('target', candidate.target_pages)):
            links = []
            for page in pages:
                if page in previews.get(side, {}):
                    links.append(f'<li><a href="#preview-{side}-{page}">{side} page {page} — aperçu PDF réel</a></li>')
                else:
                    links.append(f'<li>{side} page {page} — aperçu indisponible</li>')
            cards.append(f'<div class="candidate-side"><h3>{html.escape(side)}</h3><ul>{"".join(links)}</ul></div>')
        label = 'Division 1→2' if candidate.kind == 'split' else 'Fusion 2→1'
        sections.append(
            f'<section class="candidate" id="candidate-{index}" data-kind="{candidate.kind}">'
            f'<h3>{label} — candidat {index}</h3>'
            f'<p>Recouvrement textuel mesuré : {candidate.text_overlap:.1%}. '
            'Appariement candidat, non vérifié visuellement ; aucune certification de fidélité.</p>'
            f'<div class="candidate-grid">{"".join(cards)}</div></section>'
        )
    return '<section id="candidate-comparisons"><h2>Divisions et fusions de pages candidates</h2>' + ''.join(sections) + '</section>'
