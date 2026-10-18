"""V20.6 standalone diagnostic dashboard exporter. Author: Abdelhalim Talbi."""
from __future__ import annotations
import argparse
import base64
import html
import json
import math
from pathlib import Path

MAX_REPORT_BYTES = 25 * 1024 * 1024

from report_quality import assess_report_quality
from visual_text_correlation import correlate_visual_text
from visual_coordinate_transform import convert_raster_regions
from diagnostic_pipeline import prepare_spatial_diagnostic
from diagnostic_export import export_diagnostic


def _text(value):
    return html.escape(str(value), quote=True)


def collect_findings(report: dict) -> list[dict]:
    """Normalize independent diagnostics into traceable review items."""
    if not isinstance(report, dict):
        raise ValueError("Diagnostic must be an object")
    findings=[]
    def add(level, kind, summary, origin, side=None, page=None):
        findings.append({'severity':level,'kind':kind,'summary':str(summary)[:1000], 'origin':origin, 'side':side, 'page':page})
    for warning in report.get('warnings') or []:
        add('medium','extraction',warning,'warnings')
    if report.get('layout_comparable') is False:
        add('medium','layout','Page geometry is not directly comparable; visual scores require review','layout_comparable')
    multipage=report.get('multipage_audit') or {}
    if isinstance(multipage,dict):
        for key in ('unmatched_source','unmatched_target','missing_pages','added_pages'):
            value=multipage.get(key)
            if isinstance(value,list):
                for item in value[:200]: add('high','pagination',f'{key}: {item}',f'multipage_audit.{key}')
    # Actual R26 schema: 1-based unmatched page numbers.
    if isinstance(multipage,dict):
        for key, side in (('unmatched_source_pages','source'),('unmatched_target_pages','target'),('empty_text_source_pages','source'),('empty_text_target_pages','target')):
            values=multipage.get(key)
            if isinstance(values,list):
                for page in values[:200]:
                    if type(page) is int and 1 <= page <= 1000:
                        add('high' if key.startswith('unmatched') else 'medium','pagination',f'{key}: page {page}',f'multipage_audit.{key}',side,page)
    layout=report.get('layout_table_audit_v235') or {}
    for finding in layout.get('findings', []):
        if isinstance(finding, dict):
            add('medium','layout',f"Layout review candidate: {finding.get('kind', 'unknown')} source {finding.get('source_page')} -> target {finding.get('target_page')}",'layout_table_audit_v235.findings')
    # V24.3: only coordinates measured on actual text-matched PDF pages.
    # Do not invent regions for block counts, order changes, or unmatched pages.
    if isinstance(layout, dict):
        for finding in (layout.get('findings') or [])[:200]:
            if not isinstance(finding, dict) or finding.get('kind') != 'text_block_geometry':
                continue
            source_page, target_page = finding.get('source_page'), finding.get('target_page')
            if type(source_page) is not int or type(target_page) is not int:
                continue
            for region in (finding.get('regions') or [])[:100]:
                if not isinstance(region, dict):
                    continue
                for side, page, field in (('source',source_page,'source_bbox'),('target',target_page,'target_bbox')):
                    bbox = region.get(field)
                    if not isinstance(bbox, (list,tuple)) or len(bbox)!=4 or any(type(n) not in (int,float) or not math.isfinite(n) for n in bbox):
                        continue
                    x0,y0,x1,y1=bbox
                    if not (0<=x0<x1 and 0<=y0<y1):
                        continue
                    excerpt=str(region.get('text_excerpt',''))[:100]
                    add('medium','layout_region',f'Déplacement de bloc mesuré : {excerpt}',
                        'layout_table_audit_v235.findings.regions',side,page)
                    findings[-1]['bbox']=tuple(bbox)
    sequence=report.get('page_sequence_audit_v234') or {}
    if isinstance(sequence,dict):
        for moved in (sequence.get('moved_pages') or [])[:200]:
            if isinstance(moved,dict):
                add('medium','pagination',f"Moved text-matched page: source {moved.get('source_page')} -> target {moved.get('target_page')}",'page_sequence_audit_v234.moved_pages')
        for changed in (sequence.get('geometry_changes_on_exact_matches') or [])[:200]:
            if isinstance(changed,dict):
                add('medium','layout',f"Page geometry changed: source {changed.get('source_page')} -> target {changed.get('target_page')}",'page_sequence_audit_v234.geometry_changes_on_exact_matches')
    tables=report.get('pdf_office_table_audit') or {}
    if isinstance(tables,dict):
        for key in ('unmatched_source','unmatched_target'):
            value=tables.get(key)
            if isinstance(value,list):
                for item in value[:200]: add('high','tables',f'{key}: {item}',f'pdf_office_table_audit.{key}')
        for match in (tables.get('matches') or [])[:500]:
            if not isinstance(match,dict):continue
            for key in ('missing_rows','added_rows','missing_cells','added_cells'):
                value=match.get(key)
                if isinstance(value,list) and value:
                    add('high','tables',f'{key}: {len(value)} entries in table {match.get("source_id", "?")}',f'pdf_office_table_audit.matches.{key}')
    # Browser pipeline center has a version-dependent shape: only consume explicit items.
    diag=report.get('diagnostic') or {}
    if isinstance(diag,dict):
        center=diag.get('diagnosticCenter') or {}
        if isinstance(center,dict):
            items=center.get('items') or center.get('issues') or []
            if isinstance(items,list):
                for item in items[:3000]:
                    if not isinstance(item,dict):continue
                    raw=str(item.get('severity','low')).lower()
                    level={'critical':'high','high':'high','medium':'medium','low':'low'}.get(raw,'low')
                    add(level,'diagnostic',item.get('description') or item.get('message') or item.get('type') or 'Review anomaly','diagnostic.diagnosticCenter')
    # Explicit page-space annotations supplied by a trusted extraction pipeline.
    # Do not infer coordinates from a textual anomaly description.
    for item in (report.get('page_annotations') or [])[:500]:
        if not isinstance(item,dict):continue
        side,page=item.get('side'),item.get('page')
        bbox=item.get('bbox')
        if side not in ('source','target') or type(page) is not int or not 1<=page<=1000:continue
        if not isinstance(bbox,(list,tuple)) or len(bbox)!=4 or any(type(n) not in (int,float) or not math.isfinite(n) for n in bbox):continue
        x0,y0,x1,y1=bbox
        if not (0<=x0<x1 and 0<=y0<y1):continue
        level=item.get('severity','medium')
        if level not in ('high','medium','low'):level='medium'
        add(level,'zone',item.get('summary','Zone à vérifier'),'page_annotations',side,page)
        findings[-1]['bbox']=tuple(bbox)
    return findings[:5000]


def locate_text_differences(report: dict, pdf_paths: dict) -> list[dict]:
    """Locate explicitly supplied text fragments using PyMuPDF's actual PDF text layer.

    No OCR, guessed coordinates, or claim of semantic equivalence. Ambiguous or
    absent matches remain unlocated; limit inputs and boxes for predictable cost.
    """
    differences=report.get('text_differences', []) if isinstance(report,dict) else []
    if not isinstance(differences,list):return []
    try:
        import fitz
    except ImportError:return []
    located=[]
    for side in ('source','target'):
        path=pdf_paths.get(side)
        if path is None or not Path(path).is_file():continue
        with fitz.open(path) as doc:
            for item in differences[:100]:
                if not isinstance(item,dict) or item.get('side')!=side:continue
                n=item.get('page');fragment=item.get('text')
                if type(n) is not int or not 1<=n<=len(doc) or not isinstance(fragment,str) or not 3<=len(fragment)<=180:continue
                if any(ord(c)<32 and c not in '\t\n' for c in fragment):continue
                matches=doc[n-1].search_for(fragment,quads=False)
                # Multiple matches are ambiguous: don't pretend to know which occurrence changed.
                if len(matches)!=1:continue
                r=matches[0]
                if r.is_empty or not doc[n-1].rect.contains(r):continue
                located.append({'side':side,'page':n,'bbox':(r.x0,r.y0,r.x1,r.y1),
                                'severity':'medium','summary':'Correspondance textuelle localisée (à vérifier) : '+fragment[:120],
                                'evidence':'pdf_text_search','confidence':'exact_fragment_unique'})
    return located


def _render_pdf_previews(pdf_path:Path, page_numbers:set[int], *, max_pages=24, rectangles=None)->dict[int,str]:
    """Render real PDF pages with optional validated PDF-point bounding boxes."""
    if not pdf_path.is_file() or pdf_path.suffix.lower()!='.pdf':
        raise ValueError('Preview input must be an existing PDF')
    try:
        import fitz
    except ImportError as exc:
        raise ValueError('PyMuPDF required for page previews') from exc
    images={}
    rectangles=rectangles or {}
    with fitz.open(pdf_path) as doc:
        for n in sorted(page_numbers)[:max_pages]:
            if 1<=n<=len(doc):
                page=doc[n-1]
                pix=page.get_pixmap(matrix=fitz.Matrix(0.7,0.7),alpha=False)
                if pix.width*pix.height > 2000000:continue
                rects=rectangles.get(n,[])[:40]
                if rects:
                    from PIL import Image,ImageDraw
                    import io
                    im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
                    draw=ImageDraw.Draw(im)
                    for box in rects:
                        r=fitz.Rect(box)
                        # Coordinates are PDF points; reject off-page boxes, do not clamp silently.
                        if r.is_empty or not page.rect.contains(r):continue
                        draw.rectangle(tuple(round(v*0.7) for v in box),outline=(218,48,48),width=3)
                    output=io.BytesIO();im.save(output,format='PNG');png=output.getvalue()
                else:png=pix.tobytes('png')
                images[n]='data:image/png;base64,'+base64.b64encode(png).decode('ascii')
    return images


def align_page_pairs(report:dict, source_pages:set[int], target_pages:set[int])->list[tuple[int|None,int|None,str]]:
    """One-to-one, text-evidence page pairing; unmatched pages remain visible.

    Exact matches take precedence. Candidate matches are never presented as verified.
    Untrusted/duplicate/out-of-range pairs are ignored.
    """
    audit=report.get('multipage_audit') or {}
    if not isinstance(audit,dict):audit={}
    used_src=set();used_dst=set();pairs=[]
    for key,status in (('exact_text_page_matches','exact-text'),('candidate_text_page_matches','candidate-text')):
        values=audit.get(key) or []
        if not isinstance(values,list):continue
        for item in values[:1000]:
            if not isinstance(item,dict):continue
            a,b=item.get('source_page'),item.get('target_page')
            if type(a) is not int or type(b) is not int or a not in source_pages or b not in target_pages:continue
            if a in used_src or b in used_dst:continue
            pairs.append((a,b,status));used_src.add(a);used_dst.add(b)
    # Do not guess that two unmatched page numbers are semantically equivalent.
    pairs.extend((a,None,'unmatched-source') for a in sorted(source_pages-used_src))
    pairs.extend((None,b,'unmatched-target') for b in sorted(target_pages-used_dst))
    return pairs


def split_merge_comparison_sections(report:dict, previews:dict)->str:
    """Display 1:2 / 2:1 text candidates with real page previews when available.

    Candidates are displayed separately from confirmed 1:1 pairs. Missing images
    remain explicit. No semantic or visual equivalence is asserted.
    """
    audit=report.get('multipage_audit') or {}
    candidates=audit.get('split_merge_candidates',[]) if isinstance(audit,dict) else []
    if not isinstance(candidates,list):return ''
    sections=[];seen=set()
    for candidate in candidates[:200]:
        if not isinstance(candidate,dict) or candidate.get('type') not in ('split','merge'):continue
        source,target=candidate.get('source_pages'),candidate.get('target_pages')
        kind=candidate['type']
        if not isinstance(source,list) or not isinstance(target,list):continue
        if (len(source),len(target)) != ((1,2) if kind=='split' else (2,1)):continue
        if any(type(n) is not int or n<1 or n>1000 for n in source+target):continue
        if len(set(source))!=len(source) or len(set(target))!=len(target):continue
        score=candidate.get('text_overlap')
        if type(score) not in (float,int) or not math.isfinite(score) or not 0<=score<=1:continue
        key=(kind,tuple(source),tuple(target))
        if key in seen:continue
        seen.add(key)
        panes=[]
        for side,numbers in (('source',source),('target',target)):
            imgs=[]
            for n in numbers:
                src=previews.get(side,{}).get(n)
                if src:imgs.append(f'<figure><img loading="lazy" alt="Aperçu PDF {_text(side)} page {n}" src="{src}"><figcaption>{_text(side)} — page {n}</figcaption></figure>')
                else:imgs.append(f'<p>Aperçu indisponible : {_text(side)} page {n}</p>')
            panes.append('<div class="compare-pane">'+''.join(imgs)+'</div>')
        sections.append(f'<section class="split-merge" data-kind="{kind}"><h2>{"Division 1→2" if kind=="split" else "Fusion 2→1"} — candidat</h2><p>Pages source : {", ".join(map(str,source))} · pages cible : {", ".join(map(str,target))} · recouvrement textuel : {score:.1%}. Correspondance non certifiée.</p><div class="compare-grid">{"".join(panes)}</div></section>')
    return '<div id="split-merge"><h2>Changements de pagination candidats (1:2 / 2:1)</h2>'+''.join(sections)+'</div>' if sections else ''

def build_dashboard(report:dict, *, source_pdf:Path|None=None, target_pdf:Path|None=None)->str:
    # Only explicit, uniquely located text fragments get PDF-space rectangles.
    localized=locate_text_differences(report,{'source':source_pdf,'target':target_pdf})
    annotated=dict(report)
    annotated['page_annotations']=list(report.get('page_annotations') or [])+localized
    findings=collect_findings(annotated)
    quality=assess_report_quality(report, findings)
    spatial=prepare_spatial_diagnostic(annotated)
    mapped_regions=spatial['mapped_regions']
    correlations=spatial['correlations']
    counts={s:sum(x['severity']==s for x in findings) for s in ('high','medium','low')}
    previews={}
    for side,path in (('source',source_pdf),('target',target_pdf)):
        if path is not None:
            numbers={f['page'] for f in findings if f['side']==side and f['page'] is not None}
            rectangles={n:[f['bbox'] for f in findings if f.get('side')==side and f.get('page')==n and 'bbox' in f] for n in numbers}
            previews[side]=_render_pdf_previews(Path(path),numbers,rectangles=rectangles)
    # Render pages needed by 1:2 and 2:1 candidates, not just anomaly pages.
    audit=report.get('multipage_audit') or {}
    candidates=audit.get('split_merge_candidates',[]) if isinstance(audit,dict) else []
    if isinstance(candidates,list):
        for side,path in (('source',source_pdf),('target',target_pdf)):
            if path is None:continue
            required=set()
            for c in candidates[:200]:
                if not isinstance(c,dict):continue
                for n in c.get(side+'_pages',[]) if isinstance(c.get(side+'_pages'),list) else []:
                    if type(n) is int and 1<=n<=1000:required.add(n)
            current=previews.get(side,{})
            missing=required-set(current)
            if missing:
                # A strict combined preview cap prevents unbounded HTML growth.
                available=max(0,24-len(current))
                if available:current.update(_render_pdf_previews(Path(path),set(sorted(missing)[:available]),max_pages=available))
                previews[side]=current
    rows=[]
    for f in findings:
        location='—'
        if f['side'] and f['page'] is not None:
            anchor=f"preview-{f['side']}-{f['page']}"
            location=f'<a href="#{anchor}">{_text(f["side"])} p.{f["page"]}</a>' if f['page'] in previews.get(f['side'],{}) else f'{_text(f["side"])} p.{f["page"]} (aperçu indisponible)'
        rows.append('<tr data-side="'+_text(f.get('side') or '')+'" data-page="'+_text(f.get('page') or '')+'" data-severity="'+_text(f['severity'])+'"><td>'+_text(f['severity'])+'</td><td>'+_text(f['kind'])+'</td><td>'+_text(f['summary'])+'</td><td>'+location+'</td><td>'+_text(f['origin'])+'</td></tr>')
    if not rows:rows=['<tr><td colspan="5">No findings in the supported normalized fields. Review the JSON for other diagnostics.</td></tr>']
    # V21.7: trusted mapped regions only; bounds checked against the actual PDF page.
    region_overlays={}
    for region in mapped_regions:
        side,page,bbox=region['side'],region['page'],region['bbox']
        path={'source':source_pdf,'target':target_pdf}.get(side)
        if path is None or page not in previews.get(side,{}):continue
        try:
            import fitz
            with fitz.open(str(path)) as document:
                if page>len(document):continue
                pdfpage=document[page-1]
                if pdfpage.rotation!=0 or pdfpage.cropbox!=pdfpage.mediabox:continue
                width,height=pdfpage.rect.width,pdfpage.rect.height
            x0,y0,x1,y1=bbox
            if not (0<=x0<x1<=width and 0<=y0<y1<=height):continue
            key=(side,page)
            if len(region_overlays.get(key,[]))>=30:continue
            region_overlays.setdefault(key,[]).append((x0/width*100,y0/height*100,(x1-x0)/width*100,(y1-y0)/height*100,(x0,y0,x1,y1)))
        except (OSError,ValueError,RuntimeError,IndexError,TypeError):continue
    # Match pages using R26 text audit when present; never silently pair by index.
    sections=[]
    aligned=align_page_pairs(report,set(previews.get('source',{})),set(previews.get('target',{})))
    for index,(source_page,target_page,status) in enumerate(aligned):
        columns=[]
        for side,number in (('source',source_page),('target',target_page)):
            src=previews.get(side,{}).get(number) if number is not None else None
            if src:
                regions=region_overlays.get((side,number),[])
                outlines=''.join(f'<span class="pdf-region" data-region-index="{i+1}" role="button" tabindex="0" aria-label="Sélectionner la région vérifiée {i+1}" title="Région vérifiée {i+1}" data-pdf-bbox="{bbox[0]:.4f},{bbox[1]:.4f},{bbox[2]:.4f},{bbox[3]:.4f}" data-provenance="raster-mapping-validated" style="left:{x:.5f}%;top:{y:.5f}%;width:{w:.5f}%;height:{h:.5f}%"></span>' for i,(x,y,w,h,bbox) in enumerate(regions))
                columns.append(f'<div class="compare-pane" id="preview-{side}-{number}"><h3>{_text(side)} — page {number}</h3><div class="pdf-region-stage"><img loading="lazy" alt="Rendu réel de la page PDF {side} page {number}" src="{src}">{outlines}</div></div>')
            else:
                columns.append(f'<div class="compare-pane missing"><h3>{_text(side)} — aucune page appariée</h3><p>Aperçu indisponible</p></div>')
        description={'exact-text':'Texte identique (appariement textuel, pas visuel)',
                     'candidate-text':'Correspondance textuelle candidate — vérification requise',
                     'unmatched-source':'Page source sans correspondance confirmée',
                     'unmatched-target':'Page cible sans correspondance confirmée'}[status]
        sections.append(f'<section class="comparison" id="pair-{index}" data-page="{_text(str(source_page or "—"))} → {_text(str(target_page or "—"))}" data-pair-status="{_text(status)}"><h2>Comparaison — source {source_page or "—"} / cible {target_page or "—"}</h2><p class="alignment-status">{_text(description)}</p><div class="compare-grid">{"".join(columns)}</div><p><a href="#findings">Retour aux anomalies</a></p></section>')
    split_merge_sections=split_merge_comparison_sections(report,previews)
    template = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenPDF Studio V25.4</title><!-- Diagnostic V21.0 : identifiant historique des tests de compatibilité --><style>body{font-family:Segoe UI,Arial,sans-serif;background:#f3f6fa;color:#19324e;margin:24px}header{background:#193c65;color:white;padding:24px;border-radius:12px}.stats{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}.stat,section{background:white;border:1px solid #d4e1ee;border-radius:10px;padding:16px}table{border-collapse:collapse;width:100%;background:white}td,th{border-bottom:1px solid #d5e0e9;padding:10px;text-align:left}th{background:#dce9f7}button,select{padding:8px;margin:6px}section{margin:20px 0;scroll-margin-top:16px}section img{max-width:100%;max-height:760px;border:1px solid #d5e0e9}.compare-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.compare-pane{min-width:0;overflow:auto}.compare-pane img{display:block;width:100%;height:auto}.comparison .compare-pane{max-height:75vh;overflow:auto;scrollbar-gutter:stable}.comparison .compare-pane img{width:var(--page-zoom,100%);max-width:none;max-height:none}.zoom-status{font-variant-numeric:tabular-nums;min-width:3.5em;text-align:center}.compare-controls{flex-wrap:wrap}.split-merge figure{margin:8px 0}.split-merge figcaption{font-size:.9rem}.missing{background:#f3f6fa;padding:12px}.compare-controls{display:flex;gap:12px;align-items:center;margin:18px 0}@media(max-width:750px){.compare-grid{grid-template-columns:1fr}}tr[hidden]{display:none}input[type=search]{padding:8px;max-width:300px;width:100%}tr:focus{outline:3px solid #1965a5;outline-offset:-3px}button:focus-visible,a:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #1965a5;outline-offset:2px}.overlay-view{margin-top:16px;border:1px solid #c9d9ea;border-radius:10px;padding:12px;background:#f8fbff}.overlay-stage{position:relative;width:100%;max-width:950px;margin:auto;overflow:auto;background:#e3eaf2}.overlay-stage img{display:block;width:100%;height:auto;max-height:none;border:0}.overlay-stage img.overlay-target{position:absolute;inset:0;opacity:var(--overlay-opacity,.5);transform:translate(var(--overlay-x,0px),var(--overlay-y,0px)) scale(var(--overlay-scale,1));transform-origin:center center;pointer-events:none}.overlay-note{font-size:.9rem;color:#465c73}.difference-canvas{display:block;width:100%;max-width:950px;height:auto;margin:10px auto;border:1px solid #c9d9ea}.difference-canvas[hidden]{display:none!important}.pdf-region-stage{position:relative;display:inline-block;min-width:0;line-height:0}.pdf-region-stage img{display:block}.pdf-region{position:absolute;border:2px solid #0b84dd;background:rgba(11,132,221,.13);box-sizing:border-box;pointer-events:none}.pdf-region-stage:not(.show-regions) .pdf-region{display:none}.pdf-region-stage.show-regions .pdf-region{pointer-events:auto;cursor:pointer}.pdf-region-stage.show-regions .pdf-region:focus-visible,.pdf-region-stage.show-regions .pdf-region.is-selected{outline:3px solid #e85d04;outline-offset:2px;background:rgba(232,93,4,.25)}.correlation-jump.is-linked{outline:3px solid #e85d04;background:#fff0e5}tbody tr.is-linked{background:#fff0e5}.qualification-chart-bar{display:flex;align-items:center;gap:10px;margin:8px 0}.qualification-chart-bar span{min-width:115px}.qualification-chart-bar meter{width:min(60%,420px);height:22px}.qualification-chart-bar strong{font-variant-numeric:tabular-nums}.qualification-chart-bar:focus-within{outline:2px solid #1965a5}.overlay-stage[hidden],.overlay-view[hidden]{display:none!important}tbody tr.inspector-muted:not([hidden]){opacity:.22}tbody tr.inspector-muted:not([hidden]) td{filter:grayscale(1)}.pdf-region.region-focus-v246{outline:5px solid #e85d04!important;outline-offset:3px;background:rgba(255,166,0,.35)!important;z-index:3}.region-focus-status-v246{display:block;padding:8px 12px;margin:8px 0;border-left:4px solid #1965a5;background:#edf5ff;font-weight:600}</style></head><body><header><h1>OpenPDF Studio — Diagnostic V25.4</h1><p>Auteur : Abdelhalim Talbi</p></header><section id="difference-inspector" aria-label="Inspecteur des anomalies"><h2>Inspecteur des différences</h2><p>Navigation entre constats visibles, sans inférer une correspondance géométrique.</p><div class="compare-controls"><label for="inspector-category">Catégorie</label><select id="inspector-category"><option value="all">Toutes les catégories</option></select><label for="inspector-focus-only"><input id="inspector-focus-only" type="checkbox"> Isoler le constat sélectionné</label><button id="inspector-region" type="button" disabled>Afficher la région vérifiée</button><button id="inspector-prev" type="button">Constat précédent</button><button id="inspector-next" type="button">Constat suivant</button><output id="inspector-status" role="status" aria-live="polite">Aucun constat sélectionné</output></div><p id="inspector-detail" role="status" aria-live="polite">Sélectionnez un constat pour afficher sa page et son origine.</p></section><div class="stats"><div class="stat">Total: __TOTAL__</div><div class="stat">Élevées: __HIGH__</div><div class="stat">Moyennes: __MEDIUM__</div><div class="stat">Faibles: __LOW__</div></div><section id="qualification-overview" aria-label="Synthèse globale"><h2>Synthèse globale du diagnostic</h2><p>Statistiques descriptives uniquement : aucune certification automatique de fidélité.</p><div id="qualification-summary" role="status" aria-live="polite"></div><div id="qualification-charts"><h3>Graphiques et filtres de synthèse</h3><label for="qualification-severity-filter">Gravité</label><select id="qualification-severity-filter"><option value="all">Toutes</option><option value="high">Élevée</option><option value="medium">Moyenne</option><option value="low">Faible</option></select><label for="qualification-category-filter">Catégorie</label><select id="qualification-category-filter"><option value="all">Toutes</option></select><button id="qualification-filter-reset" type="button">Réinitialiser</button><p id="qualification-chart-count" role="status" aria-live="polite"></p><div id="qualification-severity-chart" aria-label="Répartition par gravité"></div><div id="qualification-category-chart" aria-label="Répartition par catégorie"></div></div><button id="qualification-export" type="button">Exporter la synthèse JSON</button></section><main id="findings"><label for="severity">Gravité</label><select id="severity"><option value="all">Toutes</option><option value="high">Élevée</option><option value="medium">Moyenne</option><option value="low">Faible</option></select><label for="query">Rechercher</label><input id="query" type="search" placeholder="Texte, catégorie, page…" autocomplete="off"><span id="filtered-count" aria-live="polite"></span><label for="issue-nav">Anomalie</label><select id="issue-nav" aria-label="Naviguer vers une anomalie"></select><button id="go-issue" type="button">Afficher l’anomalie</button><button id="export">Exporter CSV</button><button id="export-json" type="button">Exporter diagnostic JSON</button><table><thead><tr><th>Gravité</th><th>Catégorie</th><th>Constat</th><th>Page</th><th>Origine</th></tr></thead><tbody>__ROWS__</tbody></table></main><nav class="compare-controls" aria-label="Navigation des comparaisons"><button id="previous-pair" type="button">Page précédente</button><span id="pair-status" aria-live="polite"></span><button id="next-pair" type="button">Page suivante</button><label for="regions-visible"><input id="regions-visible" type="checkbox"> Afficher les régions vérifiées</label><output id="region-selection-status" role="status" aria-live="polite">Aucune région sélectionnée</output><button id="region-selection-previous" type="button">Région précédente</button><button id="region-selection-next" type="button">Région suivante</button><div id="region-pair-panel" role="group" aria-label="Navigation des régions par document"><button id="region-pair-source" type="button" disabled>Source : 0 région</button><button id="region-pair-target" type="button" disabled>Cible : 0 région</button><output id="region-pair-status" role="status" aria-live="polite">Aucune région vérifiée sur la paire active</output></div><output id="pair-evidence-status" role="status" aria-live="polite">Correspondance non évaluée</output><output id="region-page-context" role="status" aria-live="polite">Aucune page corrélée sélectionnée</output><output id="region-selection-details" role="status" aria-live="polite">Aucun détail disponible</output><section id="region-evidence-card" aria-label="Fiche de région vérifiée"><h2>Fiche de région</h2><p id="region-evidence-summary" role="status" aria-live="polite">Sélectionnez une région pour consulter les preuves.</p><dl id="region-evidence-fields"><dt>État</dt><dd>Sélectionnez une région vérifiée</dd></dl></section><button id="region-selection-clear" type="button">Effacer la sélection</button><span aria-label="Zoom des pages">Zoom :</span><button id="zoom-out" type="button" aria-label="Réduire le zoom">−</button><output id="zoom-status" class="zoom-status" aria-live="polite">100 %</output><button id="zoom-in" type="button" aria-label="Augmenter le zoom">+</button><button id="zoom-reset" type="button">Réinitialiser</button><label for="sync-scroll"><input id="sync-scroll" type="checkbox" checked> Défilement synchronisé</label></nav><section id="overlay-panel" class="overlay-view" aria-label="Superposition visuelle" hidden><h2>Superposition source / cible</h2><p class="overlay-note">Superposition géométrique indicative, avec décalage manuel facultatif (aucun recalage automatique sans validation). Les différences de dimensions et les décalages de page peuvent fausser l'interprétation.</p><label for="overlay-opacity">Opacité cible</label><input id="overlay-opacity" type="range" min="0" max="100" value="50" step="5"><output id="overlay-value" for="overlay-opacity">50 %</output><label for="overlay-x">Décalage horizontal (px)</label><input id="overlay-x" type="range" min="-150" max="150" value="0" step="1"><output id="overlay-x-value" for="overlay-x">0 px</output><label for="overlay-y">Décalage vertical (px)</label><input id="overlay-y" type="range" min="-150" max="150" value="0" step="1"><output id="overlay-y-value" for="overlay-y">0 px</output><label for="overlay-scale">Échelle cible (%)</label><input id="overlay-scale" type="range" min="90" max="110" value="100" step="1"><output id="overlay-scale-value" for="overlay-scale">100 %</output><button id="overlay-reset" type="button">Réinitialiser le recalage</button><button id="overlay-auto" type="button">Proposer un recalage automatique</button><output id="overlay-auto-status" role="status" aria-live="polite">Non analysé</output><div id="overlay-stage" class="overlay-stage"><img id="overlay-source" alt="Page PDF source"><img id="overlay-target" class="overlay-target" alt="Page PDF cible"></div><div class="difference-controls"><button id="difference-render" type="button">Visualiser les écarts après recalage</button><label for="difference-threshold">Seuil de différence</label><input id="difference-threshold" type="range" min="10" max="100" value="35" step="5"><output id="difference-threshold-value">35</output><output id="difference-status" role="status" aria-live="polite">Non analysé</output></div><canvas id="difference-canvas" class="difference-canvas" width="384" height="384" hidden aria-label="Carte des différences géométriques"></canvas><p id="overlay-warning" role="status"></p></section><nav><label for="overlay-enabled"><input type="checkbox" id="overlay-enabled"> Activer la superposition des pages appariées</label></nav><div id="previews">__PREVIEWS__</div>__SPLIT_MERGE__<p>Résultats heuristiques, revue humaine nécessaire. Les aperçus sont des rendus de pages PDF, pas des captures de l'interface. Les cadres rouges proviennent uniquement de coordonnées explicites du diagnostic. L’appariement utilise uniquement les correspondances textuelles R26 présentes dans le JSON ; les pages non appariées restent séparées. Le recalage manuel ne prouve pas la fidélité visuelle. Aucun envoi réseau.</p><script>const pairs=[...document.querySelectorAll('.comparison')];let activePair=0;function showPair(i){if(!pairs.length){document.getElementById('pair-status').textContent='Aucun aperçu';return;}activePair=Math.max(0,Math.min(i,pairs.length-1));pairs.forEach((p,j)=>p.hidden=j!==activePair);document.getElementById('pair-status').textContent='Comparaison '+(activePair+1)+' / '+pairs.length+' — page '+pairs[activePair].dataset.page;document.getElementById('previous-pair').disabled=activePair===0;document.getElementById('next-pair').disabled=activePair===pairs.length-1;}document.getElementById('previous-pair').addEventListener('click',()=>showPair(activePair-1));document.getElementById('next-pair').addEventListener('click',()=>showPair(activePair+1));showPair(0);document.querySelectorAll('a[href^=\"#preview-\"]').forEach(a=>a.addEventListener('click',()=>{const id=a.getAttribute('href').slice(1);const pane=document.getElementById(id);if(pane){const pair=pane.closest('.comparison');const idx=pairs.indexOf(pair);if(idx>=0){showPair(idx);pair.scrollIntoView({block:'start',behavior:'smooth'});}}}));const rows=[...document.querySelectorAll('tbody tr[data-severity]')];const issueNav=document.getElementById('issue-nav');const issueButton=document.getElementById('go-issue');function populateIssues(){const selected=issueNav.value;issueNav.replaceChildren();rows.forEach((r,i)=>{if(r.hidden)return;const o=document.createElement('option');o.value=String(i);o.textContent=(i+1)+' — '+r.cells[1].textContent+' : '+r.cells[2].textContent.slice(0,90);issueNav.append(o)});if([...issueNav.options].some(o=>o.value===selected))issueNav.value=selected;issueButton.disabled=!issueNav.options.length;}issueButton.addEventListener('click',()=>{const row=rows[Number(issueNav.value)];if(!row||row.hidden)return;row.scrollIntoView({block:'center',behavior:'smooth'});row.focus();const a=row.querySelector('a[href^=\"#preview-\"]');if(a){const pane=document.getElementById(a.getAttribute('href').slice(1));const pair=pane?.closest('.comparison');const idx=pairs.indexOf(pair);if(idx>=0){showPair(idx);pair.scrollIntoView({block:'start',behavior:'smooth'});}}});rows.forEach(r=>r.tabIndex=-1);const select=document.getElementById('severity');const query=document.getElementById('query');function filterFindings(){const term=query.value.trim().toLocaleLowerCase();let visible=0;rows.forEach(r=>{const matchSeverity=select.value==='all'||r.dataset.severity===select.value;const matchText=!term||r.textContent.toLocaleLowerCase().includes(term);const chartSeverity=document.getElementById('qualification-severity-filter')?.value||'all';const chartCategory=document.getElementById('qualification-category-filter')?.value||'all';const inspectorCategory=document.getElementById('inspector-category')?.value||'all';const matchInspectorCategory=inspectorCategory==='all'||r.cells[1]?.textContent.trim()===inspectorCategory;const matchChart=(chartSeverity==='all'||r.dataset.severity===chartSeverity)&&(chartCategory==='all'||r.cells[1]?.textContent.trim()===chartCategory);r.hidden=!(matchSeverity&&matchText&&matchChart&&matchInspectorCategory);if(!r.hidden)visible++;});document.getElementById('filtered-count').textContent=visible+' / '+rows.length+' anomalies affichées';populateIssues();document.dispatchEvent(new Event('openpdf:findings-filtered'));}select.addEventListener('change',filterFindings);query.addEventListener('input',filterFindings);filterFindings();document.getElementById('export').addEventListener('click',()=>{const data=[['Gravité','Catégorie','Constat','Page','Origine'],...rows.filter(r=>!r.hidden).map(r=>[...r.cells].map(c=>c.textContent))].map(row=>row.map(v=>'"'+v.replaceAll('"','""')+'"').join(',')).join('\\r\\n');const blob=new Blob([data],{type:'text/csv;charset=utf-8'});const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download='openpdf-diagnostic-v25.4.csv';a.click();URL.revokeObjectURL(u)});const zoomLevels=[50,75,100,125,150,200,250,300];let zoomIndex=2;const zoomStatus=document.getElementById('zoom-status');function applyZoom(){const pct=zoomLevels[zoomIndex];document.querySelectorAll('.comparison .compare-pane').forEach(p=>p.style.setProperty('--page-zoom',pct+'%'));zoomStatus.textContent=pct+' %';document.getElementById('zoom-out').disabled=zoomIndex===0;document.getElementById('zoom-in').disabled=zoomIndex===zoomLevels.length-1;}document.getElementById('zoom-in').addEventListener('click',()=>{zoomIndex=Math.min(zoomIndex+1,zoomLevels.length-1);applyZoom();});document.getElementById('zoom-out').addEventListener('click',()=>{zoomIndex=Math.max(zoomIndex-1,0);applyZoom();});document.getElementById('zoom-reset').addEventListener('click',()=>{zoomIndex=2;applyZoom();});applyZoom();let syncingScroll=false;document.querySelectorAll('.comparison').forEach(pair=>{const panes=[...pair.querySelectorAll('.compare-pane:not(.missing)')];if(panes.length!==2)return;panes.forEach((pane,i)=>pane.addEventListener('scroll',()=>{if(syncingScroll||!document.getElementById('sync-scroll').checked||pair.hidden)return;const other=panes[1-i];const yMax=pane.scrollHeight-pane.clientHeight;const xMax=pane.scrollWidth-pane.clientWidth;const yRatio=yMax>0?pane.scrollTop/yMax:0;const xRatio=xMax>0?pane.scrollLeft/xMax:0;syncingScroll=true;other.scrollTop=yRatio*Math.max(0,other.scrollHeight-other.clientHeight);other.scrollLeft=xRatio*Math.max(0,other.scrollWidth-other.clientWidth);syncingScroll=false;}));});const overlayEnabled=document.getElementById('overlay-enabled');const overlayPanel=document.getElementById('overlay-panel');const overlayOpacity=document.getElementById('overlay-opacity');const overlayValue=document.getElementById('overlay-value');const overlaySource=document.getElementById('overlay-source');const overlayTarget=document.getElementById('overlay-target');const overlayWarning=document.getElementById('overlay-warning');function updateOverlay(){const pair=pairs[activePair];const panes=pair?[...pair.querySelectorAll('.compare-pane:not(.missing)')]:[];const imgs=panes.map(p=>p.querySelector('img'));const valid=panes.length===2&&imgs.every(Boolean);overlayPanel.hidden=!overlayEnabled.checked||!valid;if(!valid){overlayWarning.textContent='';return;}overlaySource.src=imgs[0].src;overlayTarget.src=imgs[1].src;overlayWarning.textContent='Attention : recalage manuel indicatif, sans vérification automatique de l’échelle ni des contenus.';}overlayEnabled.addEventListener('change',updateOverlay);overlayOpacity.addEventListener('input',()=>{const pct=Number(overlayOpacity.value);document.getElementById('overlay-stage').style.setProperty('--overlay-opacity',String(pct/100));overlayValue.textContent=pct+' %';});const offsetX=document.getElementById('overlay-x');const offsetY=document.getElementById('overlay-y');const overlayStage=document.getElementById('overlay-stage');const scaleInput=document.getElementById('overlay-scale');function updateScale(){const n=Number(scaleInput.value);const safe=Number.isFinite(n)?Math.max(90,Math.min(110,n)):100;overlayStage.style.setProperty('--overlay-scale',String(safe/100));document.getElementById('overlay-scale-value').textContent=safe+' %';}scaleInput.addEventListener('input',updateScale);updateScale();function updateOffset(){for(const [input,axis] of [[offsetX,'x'],[offsetY,'y']]){const n=Number(input.value);const safe=Number.isFinite(n)?Math.max(-150,Math.min(150,n)):0;overlayStage.style.setProperty('--overlay-'+axis,safe+'px');document.getElementById('overlay-'+axis+'-value').textContent=safe+' px';}}offsetX.addEventListener('input',updateOffset);offsetY.addEventListener('input',updateOffset);document.getElementById('overlay-reset').addEventListener('click',()=>{offsetX.value='0';offsetY.value='0';scaleInput.value='100';updateScale();updateOffset();});updateOffset();const originalShowPair=showPair;showPair=function(i){originalShowPair(i);updateOverlay();};updateOverlay();__AUTOALIGN_SCRIPT__ __DIFFERENCE_SCRIPT__ __EVIDENCE_EXPORT__ __CORRELATION_NAV__ __REGION_OVERLAY__ __REGION_SYNC__ __REGION_EVIDENCE__ __BIDIRECTIONAL_NAV__ __QUALIFICATION_OVERVIEW__ __QUALIFICATION_CHARTS__ __DIFFERENCE_INSPECTOR__ __PAIR_EVIDENCE_V241__ __REGION_PAIR_V243__ __REGION_PROOF_V244__ __PROOF_READABILITY_V245__ __REGION_FOCUS_V246__ __REGION_CENTER_V247__ __REGION_KEYBOARD_V248__ __PAGE_KEYBOARD_V249__ __PAGE_EVIDENCE_V250__ __MULTIPAGE_GUARD_V251__ __PROOF_EXPORT_V252__ __PROOF_AUDIT_V253__ __PROOF_INTEGRITY_V254__</script></body></html>"""
    quality_html='<section id="quality" aria-label="Qualité du diagnostic"><h2>Fiabilité du diagnostic</h2><p>'+_text(quality["label"])+' — '+_text(quality["explanation"])+'</p><ul>'+''.join('<li>'+_text(note)+'</li>' for note in quality["limitations"])+'</ul></section>'
    correlation_html='<section id="spatial-correlations"><h2>Corrélation texte / régions visuelles</h2><p>Chevauchement spatial uniquement, sans classification sémantique. Coordonnées PDF explicites requises.</p>'
    if correlations:
        correlation_html+='<ol id="correlation-list">'+''.join('<li><button type="button" class="correlation-jump" data-side="'+_text(c['side'])+'" data-page="'+str(c['page'])+'">'+_text(c['side'])+' page '+str(c['page'])+' — intersection IoU '+str(c['iou'])+'</button></li>' for c in correlations)+'</ol><output id="correlation-navigation-status" role="status" aria-live="polite"></output>'
    else:
        correlation_html+='<p>Aucune corrélation vérifiable disponible : coordonnées PDF absentes ou sans intersection.</p>'
    correlation_html+='<p>Régions raster vérifiées et converties : '+str(len(mapped_regions))+'. Rejets de géométrie/provenance : '+str(sum(spatial['rejections'].values()))+'. Les régions calculées uniquement dans le navigateur ne sont pas converties automatiquement. Rotation et recadrage non pris en charge.</p></section>'
    template=template.replace('<section id="qualification-overview" aria-label="Synthèse globale"><h2>Synthèse globale du diagnostic</h2><p>Statistiques descriptives uniquement : aucune certification automatique de fidélité.</p><div id="qualification-summary" role="status" aria-live="polite"></div><div id="qualification-charts"><h3>Graphiques et filtres de synthèse</h3><label for="qualification-severity-filter">Gravité</label><select id="qualification-severity-filter"><option value="all">Toutes</option><option value="high">Élevée</option><option value="medium">Moyenne</option><option value="low">Faible</option></select><label for="qualification-category-filter">Catégorie</label><select id="qualification-category-filter"><option value="all">Toutes</option></select><button id="qualification-filter-reset" type="button">Réinitialiser</button><p id="qualification-chart-count" role="status" aria-live="polite"></p><div id="qualification-severity-chart" aria-label="Répartition par gravité"></div><div id="qualification-category-chart" aria-label="Répartition par catégorie"></div></div><button id="qualification-export" type="button">Exporter la synthèse JSON</button></section><main id="findings">',quality_html+correlation_html+'<section id="qualification-overview" aria-label="Synthèse globale"><h2>Synthèse globale du diagnostic</h2><p>Statistiques descriptives uniquement : aucune certification automatique de fidélité.</p><div id="qualification-summary" role="status" aria-live="polite"></div><div id="qualification-charts"><h3>Graphiques et filtres de synthèse</h3><label for="qualification-severity-filter">Gravité</label><select id="qualification-severity-filter"><option value="all">Toutes</option><option value="high">Élevée</option><option value="medium">Moyenne</option><option value="low">Faible</option></select><label for="qualification-category-filter">Catégorie</label><select id="qualification-category-filter"><option value="all">Toutes</option></select><button id="qualification-filter-reset" type="button">Réinitialiser</button><p id="qualification-chart-count" role="status" aria-live="polite"></p><div id="qualification-severity-chart" aria-label="Répartition par gravité"></div><div id="qualification-category-chart" aria-label="Répartition par catégorie"></div></div><button id="qualification-export" type="button">Exporter la synthèse JSON</button></section><main id="findings">')
    # JSON encoded as a JavaScript string literal, not raw HTML; escape angle brackets
    # to prevent hostile report data from closing the script element.
    evidence=export_diagnostic(annotated)
    encoded=json.dumps(evidence,ensure_ascii=False,sort_keys=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    js='const diagnosticEvidence='+encoded+';document.getElementById("export-json").addEventListener("click",()=>{const blob=new Blob([JSON.stringify(diagnosticEvidence,null,2)],{type:"application/json;charset=utf-8"});const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;a.download="openpdf-diagnostic-v25.3.json";a.click();URL.revokeObjectURL(u)});'
    template=template.replace('__EVIDENCE_EXPORT__',js)
    template=template.replace('__AUTOALIGN_SCRIPT__',Path(__file__).with_name('auto_align.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_OVERLAY__',Path(__file__).with_name('region_overlay.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_SYNC__',Path(__file__).with_name('region_sync.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_EVIDENCE__',Path(__file__).with_name('region_evidence.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_PAIR_V243__',Path(__file__).with_name('region_pair_v243.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_PROOF_V244__',Path(__file__).with_name('region_proof_v244.js').read_text(encoding='utf-8'))
    template=template.replace('__PROOF_READABILITY_V245__',Path(__file__).with_name('proof_readability_v245.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_KEYBOARD_V248__',Path(__file__).with_name('region_keyboard_v248.js').read_text(encoding='utf-8'))
    template=template.replace('__PAGE_KEYBOARD_V249__',Path(__file__).with_name('page_keyboard_v249.js').read_text(encoding='utf-8'))
    template=template.replace('__PAGE_EVIDENCE_V250__',Path(__file__).with_name('page_evidence_v250.js').read_text(encoding='utf-8'))
    template=template.replace('__MULTIPAGE_GUARD_V251__',Path(__file__).with_name('multipage_guard_v251.js').read_text(encoding='utf-8'))
    template=template.replace('__PROOF_EXPORT_V252__',Path(__file__).with_name('proof_export_v252.js').read_text(encoding='utf-8'))
    template=template.replace('__PROOF_INTEGRITY_V254__',Path(__file__).with_name('proof_integrity_v254.js').read_text(encoding='utf-8'))
    template=template.replace('__PROOF_AUDIT_V253__',Path(__file__).with_name('proof_audit_v253.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_FOCUS_V246__',Path(__file__).with_name('region_focus_v246.js').read_text(encoding='utf-8'))
    template=template.replace('__REGION_CENTER_V247__',Path(__file__).with_name('region_center_v247.js').read_text(encoding='utf-8'))
    template=template.replace('__BIDIRECTIONAL_NAV__',Path(__file__).with_name('bidirectional_navigation.js').read_text(encoding='utf-8'))
    template=template.replace('__QUALIFICATION_OVERVIEW__',Path(__file__).with_name('qualification_overview.js').read_text(encoding='utf-8'))
    template=template.replace('__QUALIFICATION_CHARTS__',Path(__file__).with_name('qualification_charts.js').read_text(encoding='utf-8'))
    template=template.replace('__CORRELATION_NAV__',Path(__file__).with_name('correlation_navigation.js').read_text(encoding='utf-8'))
    template=template.replace('__DIFFERENCE_INSPECTOR__',Path(__file__).with_name('difference_inspector_v240.js').read_text(encoding='utf-8'))
    template=template.replace('__PAIR_EVIDENCE_V241__',Path(__file__).with_name('pair_evidence_v242.js').read_text(encoding='utf-8'))
    template=template.replace('__DIFFERENCE_SCRIPT__',Path(__file__).with_name('difference_regions.js').read_text(encoding='utf-8')+'\n'+Path(__file__).with_name('difference_map.js').read_text(encoding='utf-8'))
    return (template.replace('__TOTAL__',str(len(findings))).replace('__HIGH__',str(counts['high'])).replace('__MEDIUM__',str(counts['medium'])).replace('__LOW__',str(counts['low'])).replace('__ROWS__',''.join(rows)).replace('__PREVIEWS__',''.join(sections)).replace('__SPLIT_MERGE__',split_merge_sections))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Export an offline HTML diagnostic dashboard')
    parser.add_argument('input',type=Path,help='JSON produced by compare_documents')
    parser.add_argument('output',type=Path,help='Output HTML file')
    parser.add_argument('--source-pdf',type=Path,help='Optional PDF for real source page previews')
    parser.add_argument('--target-pdf',type=Path,help='Optional PDF for real target page previews')
    args=parser.parse_args(argv)
    if args.input.stat().st_size>MAX_REPORT_BYTES:parser.error('Report exceeds 25 MiB')
    data=json.loads(args.input.read_text(encoding='utf-8'))
    args.output.write_text(build_dashboard(data,source_pdf=args.source_pdf,target_pdf=args.target_pdf),encoding='utf-8')

if __name__=='__main__':main()
