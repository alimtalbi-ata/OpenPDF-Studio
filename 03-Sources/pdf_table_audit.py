"""Heuristic PDF table extraction and content-based matching. Author: Abdelhalim Talbi.

No claim of guaranteed table structure fidelity: PDF often has no table semantics.
"""
from __future__ import annotations
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import re


def _norm(value):
    return ' '.join(str(value or '').casefold().split())


def _tokens(table):
    return Counter(_norm(cell) for row in table.get('cells', []) for cell in row if _norm(cell))


def _similarity(a, b):
    ta, tb = _tokens(a), _tokens(b)
    common = sum((ta & tb).values())
    total = sum(ta.values()) + sum(tb.values())
    content = 2 * common / total if total else 0.0
    ah = ' '.join(_norm(v) for v in a.get('header', []))
    bh = ' '.join(_norm(v) for v in b.get('header', []))
    header = SequenceMatcher(None, ah, bh).ratio() if ah and bh else 0.0
    ac, bc = a.get('columns', 0), b.get('columns', 0)
    columns = min(ac, bc) / max(ac, bc) if max(ac, bc) else 0.0
    return round(.75 * content + .15 * header + .10 * columns, 4)


def inspect_pdf_tables(path, *, max_pages=1000, max_tables=1000):
    """Use PyMuPDF find_tables where supported; no fabricated table on failure."""
    import fitz
    p = Path(path)
    if not p.is_file() or p.suffix.lower() != '.pdf':
        raise ValueError('PDF input required')
    if p.stat().st_size > 50 * 1024 * 1024:
        raise ValueError('PDF exceeds 50 MiB')
    output, warnings = [], []
    with fitz.open(str(p)) as doc:
        if doc.needs_pass:
            raise ValueError('Encrypted PDF requires unlocked input')
        if len(doc) > max_pages:
            raise ValueError('PDF exceeds page limit')
        for page_number, page in enumerate(doc, 1):
            if not hasattr(page, 'find_tables'):
                warnings.append('Installed PyMuPDF does not support find_tables')
                break
            try:
                found = page.find_tables()
            except Exception as exc:
                warnings.append(f'Page {page_number}: table detection failed ({type(exc).__name__})')
                continue
            for index, table in enumerate(found.tables, 1):
                if len(output) >= max_tables:
                    warnings.append('Table count limit reached')
                    return {'tables': output, 'warnings': warnings}
                cells = [[str(cell or '').strip() for cell in row] for row in table.extract()]
                if not cells or not any(any(row) for row in cells):
                    continue
                output.append({'id': f'pdf-p{page_number}-t{index}', 'page': page_number,
                               'rows': len(cells), 'columns': max(map(len, cells)),
                               'header': cells[0], 'cells': cells, 'source': 'pdf_heuristic'})
    return {'tables': output, 'warnings': warnings}


def match_tables(source, target, *, threshold=.55):
    """One-to-one greedy matching; unmatched tables are candidates, not proven losses."""
    if not 0 <= threshold <= 1:
        raise ValueError('threshold must be in [0,1]')
    pairs = sorted((( _similarity(a, b), i, j) for i, a in enumerate(source)
                    for j, b in enumerate(target)), reverse=True)
    used_source, used_target, matches = set(), set(), []
    for confidence, i, j in pairs:
        if confidence < threshold or i in used_source or j in used_target:
            continue
        used_source.add(i); used_target.add(j)
        a, b = source[i], target[j]
        missing = list((_tokens(a) - _tokens(b)).elements())
        added = list((_tokens(b) - _tokens(a)).elements())
        matches.append({'source_id': a['id'], 'target_id': b['id'],
                        'confidence': confidence, 'missing_cells': missing[:100],
                        'added_cells': added[:100],
                        'source_columns': a['columns'], 'target_columns': b['columns']})
    return {'matches': matches,
            'unmatched_source': [t['id'] for i, t in enumerate(source) if i not in used_source],
            'unmatched_target': [t['id'] for j, t in enumerate(target) if j not in used_target],
            'limitations': 'Heuristic PDF table extraction and content matching; unmatched tables and cells require human review. No OCR.'}


def compare_pdf_office_tables(source_path, target_path, *, threshold=.55):
    from table_structure_audit import inspect_office_tables
    source_pdf = Path(source_path).suffix.lower() == '.pdf'
    target_pdf = Path(target_path).suffix.lower() == '.pdf'
    if source_pdf == target_pdf:
        raise ValueError('Exactly one input must be PDF')
    pdf_path = source_path if source_pdf else target_path
    office_path = target_path if source_pdf else source_path
    if Path(office_path).suffix.lower() not in ('.docx', '.xlsx'):
        raise ValueError('DOCX or XLSX native tables required')
    extracted = inspect_pdf_tables(pdf_path)
    office = inspect_office_tables(office_path)
    comparison = match_tables(extracted['tables'], office, threshold=threshold) if source_pdf else match_tables(office, extracted['tables'], threshold=threshold)
    from table_fragment_audit import audit_pdf_table_fragments
    fragment_audit = audit_pdf_table_fragments(extracted['tables'])
    from consolidated_table_compare import compare_consolidated_tables
    consolidated = compare_consolidated_tables(extracted['tables'], office, threshold=threshold)
    return {'consolidated_table_comparison': consolidated, 'pdf_fragment_audit': fragment_audit, 'pdf_table_count': len(extracted['tables']), 'office_table_count': len(office),
            'pdf_warnings': extracted['warnings'], **comparison}
