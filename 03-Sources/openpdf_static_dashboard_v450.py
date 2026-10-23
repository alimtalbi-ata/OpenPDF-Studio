"""V45.0 offline diagnostic fallback when historical JS assets are unavailable.

Author: Abdelhalim Talbi.

This is intentionally a *read-only* HTML report. It never pretends to provide
interactive comparisons, automatic alignment, or fidelity certification.
"""
from __future__ import annotations

import html
from pathlib import Path

from report_quality import assess_report_quality
from openpdf_preview_budget_v453 import PreviewBudget
from openpdf_static_comparison_v454 import (extract_candidates, missing_candidate_pages,
                                             render_candidate_navigation)

# A static report is useful even if the 24 legacy JavaScript assets are absent.
# In particular, do not create placeholder JS files that make broken controls
# appear to work or silently drop warnings about missing functionality.
REQUIRED_DASHBOARD_JS = (
    'auto_align.js', 'region_overlay.js', 'region_sync.js',
    'region_evidence.js', 'region_pair_v243.js', 'region_proof_v244.js',
    'proof_readability_v245.js', 'region_keyboard_v248.js',
    'page_keyboard_v249.js', 'page_evidence_v250.js',
    'multipage_guard_v251.js', 'proof_export_v252.js',
    'proof_integrity_v254.js', 'proof_audit_v253.js',
    'region_focus_v246.js', 'region_center_v247.js',
    'bidirectional_navigation.js', 'qualification_overview.js',
    'qualification_charts.js', 'correlation_navigation.js',
    'difference_inspector_v240.js', 'pair_evidence_v242.js',
    'difference_regions.js', 'difference_map.js',
)


def missing_dashboard_assets(source_dir: Path | None = None) -> tuple[str, ...]:
    """Report exactly which bundled assets are unavailable (never download JS)."""
    folder = Path(source_dir) if source_dir is not None else Path(__file__).resolve().parent
    return tuple(name for name in REQUIRED_DASHBOARD_JS if not (folder / name).is_file())


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_static_dashboard(report: dict, *, source_pdf: Path | None = None,
                           target_pdf: Path | None = None,
                           missing_assets: tuple[str, ...] | None = None) -> str:
    """Produce a real, offline, CSP-restricted report with honest limitations.

    Page images are generated from the supplied PDFs, not mock screenshots.
    Links are internal document anchors only. No JS or external dependencies.
    """
    if not isinstance(report, dict):
        raise ValueError('Diagnostic report must be a JSON object')
    # Import lazily to avoid changing legacy dashboard initialization.
    from diagnostic_dashboard import collect_findings, _render_pdf_previews

    findings = collect_findings(report)
    quality = assess_report_quality(report, findings)
    missing = missing_dashboard_assets() if missing_assets is None else missing_assets
    counts = {level: sum(item['severity'] == level for item in findings)
              for level in ('high', 'medium', 'low')}
    # Render only explicitly referenced pages; never invent page matches.
    previews: dict[str, dict[int, str]] = {}
    preview_budget = PreviewBudget(max_pages=24)
    for side, path in (('source', source_pdf), ('target', target_pdf)):
        if path is None:
            continue
        numbers = {item['page'] for item in findings
                   if item.get('side') == side and type(item.get('page')) is int}
        previews[side] = _render_pdf_previews(Path(path), numbers, max_pages=12,
                                              budget=preview_budget)

    # V45.4: include explicit 1:2 / 2:1 candidates in offline reports.
    # Reuse anomaly previews and the same global budget; never rasterize twice.
    candidates = extract_candidates(report)
    for side, numbers in missing_candidate_pages(candidates, previews).items():
        path = source_pdf if side == 'source' else target_pdf
        if path is None or not numbers or not preview_budget.available:
            continue
        available = min(len(numbers), preview_budget.remaining_pages)
        if available:
            previews.setdefault(side, {}).update(_render_pdf_previews(
                Path(path), set(numbers[:available]), max_pages=available,
                budget=preview_budget))
    candidate_navigation = render_candidate_navigation(candidates, previews)

    def location(item: dict) -> str:
        side, page = item.get('side'), item.get('page')
        if side not in ('source', 'target') or type(page) is not int:
            return 'Non localisé'
        if page in previews.get(side, {}):
            return f'<a href="#preview-{side}-{page}">{side} page {page}</a>'
        return f'{side} page {page} (aperçu indisponible)'

    rows = ''.join(
        '<tr><td>' + _escape(item['severity']) + '</td><td>' + _escape(item['kind']) +
        '</td><td>' + _escape(item['summary']) + '</td><td>' + location(item) +
        '</td><td>' + _escape(item['origin']) + '</td></tr>'
        for item in findings
    ) or '<tr><td colspan="5">Aucune anomalie normalisée disponible.</td></tr>'

    images = ''.join(
        f'<section id="preview-{side}-{page}"><h2>{side} - page {page}</h2>'
        f'<img loading="lazy" alt="Rendu réel du PDF {side} page {page}" src="{data}">'
        '<p><a href="#findings">Retour aux anomalies</a></p></section>'
        for side in ('source', 'target')
        for page, data in sorted(previews.get(side, {}).items())
    )
    limitation_items = ''.join('<li>' + _escape(item) + '</li>'
                               for item in quality['limitations'])
    missing_note = (
        f'{len(missing)} module(s) JavaScript requis sont absents du paquet. '
        'Fonctions interactives, recalage, graphiques et navigation avancée désactivés. '
        'Aucune certification de fidélité ni comparaison visuelle automatisée.'
        if missing else 'Rapport statique explicitement demandé : interactions désactivées.'
    )
    # CSP blocks execution even if untrusted input contains an HTML injection bug.
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        'img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
        '<title>OpenPDF Studio - diagnostic statique V45.0</title>'
        '<style>body{font:16px Segoe UI,Arial,sans-serif;color:#17324d;background:#f3f6fa;'
        'margin:2rem auto;max-width:1100px;padding:0 1rem}header{background:#183e67;'
        'color:white;padding:1.5rem;border-radius:12px}section{background:white;'
        'padding:1rem;margin:1rem 0;border:1px solid #d4e1ee;border-radius:9px}'
        'table{border-collapse:collapse;width:100%;background:white}th,td{padding:.6rem;'
        'border:1px solid #d4e1ee;text-align:left;vertical-align:top}th{background:#e5edf7}'
        'img{max-width:100%;height:auto}.notice{border-left:6px solid #ae6315}'
        'a{color:#105ca3}a:focus-visible{outline:3px solid #105ca3}'
        '.candidate-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1rem}'
        '.candidate-side{border:1px solid #d4e1ee;border-radius:8px;padding:.5rem 1rem}'
        'section:target{outline:3px solid #105ca3}'
        '@media(max-width:700px){table{display:block;overflow-x:auto}}</style></head><body>'
        '<header><h1>OpenPDF Studio - diagnostic statique V45.0</h1>'
        '<p>Rapport local sans JavaScript - auteur : Abdelhalim Talbi</p></header>'
        '<section class="notice" role="status"><h2>Mode dégradé documenté</h2><p>' +
        _escape(missing_note) + '</p></section>'
        '<section aria-label="Synthèse"><h2>Résultats observés</h2><p>' +
        f'{len(findings)} anomalie(s) : {counts["high"]} élevée(s), '
        f'{counts["medium"]} moyenne(s), {counts["low"]} faible(s).</p>'
        '<p>' + _escape(quality['label']) + ' - ' + _escape(quality['explanation']) +
        '</p><ul>' + limitation_items + '</ul></section>'
        '<section id="findings"><h2>Anomalies documentées</h2><table><thead><tr>'
        '<th>Gravité</th><th>Type</th><th>Observation</th><th>Localisation</th>'
        '<th>Origine</th></tr></thead><tbody>' + rows + '</tbody></table></section>' +
        images + candidate_navigation + '<footer><p>Rendus intégrés issus des PDF fournis lorsqu’ils sont disponibles. '
        'Aucune preuve ni capture simulée.</p></footer></body></html>'
    )
