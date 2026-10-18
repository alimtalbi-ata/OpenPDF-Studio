"""Conservative cross-page PDF table continuation candidates. Abdelhalim Talbi.

Never merge tables across page gaps or claim structural identity from text alone.
"""
from __future__ import annotations
from difflib import SequenceMatcher
import math


def _norm(value):
    return ' '.join(str(value or '').casefold().split())


def _header(table):
    return tuple(_norm(v) for v in table.get('header', []))


def _rows(table):
    return [[str(v or '').strip() for v in row] for row in table.get('cells', [])]


def _header_similarity(a, b):
    x, y = _header(a), _header(b)
    if not x or not y or not any(x) or not any(y):
        return 0.0
    if x == y:
        return 1.0
    return SequenceMatcher(None, '\x1f'.join(x), '\x1f'.join(y)).ratio()


def audit_pdf_table_fragments(tables, *, min_header_similarity=0.85):
    """Group adjacent-page candidates, preserving original tables and provenance.

    A repeated header is required to create a group; otherwise report an
    ambiguous adjacency for manual inspection. Only consecutive pages qualify.
    """
    if not isinstance(tables, list) or len(tables) > 1000:
        raise ValueError('Expected a list of at most 1000 tables')
    if not isinstance(min_header_similarity, (float, int)) or not math.isfinite(min_header_similarity) or not 0 <= min_header_similarity <= 1:
        raise ValueError('min_header_similarity must be finite in [0,1]')
    seen = set()
    ordered = []
    for t in tables:
        if not isinstance(t, dict) or not isinstance(t.get('id'), str) or not t['id'] or t['id'] in seen:
            raise ValueError('Each table needs a unique nonempty id')
        seen.add(t['id'])
        page = t.get('page')
        cols = t.get('columns')
        if not isinstance(page, int) or isinstance(page, bool) or page < 1 or not isinstance(cols, int) or isinstance(cols, bool) or cols < 1:
            raise ValueError('Invalid page or column count')
        ordered.append(t)
    ordered.sort(key=lambda t: (t['page'], t['id']))
    # Multiple tables on either page make continuation ambiguous; do not auto-group.
    counts = {}
    for t in ordered:
        counts[t['page']] = counts.get(t['page'], 0) + 1
    edges, ambiguous = [], []
    for a, b in zip(ordered, ordered[1:]):
        if b['page'] != a['page'] + 1 or a['columns'] != b['columns']:
            continue
        similarity = _header_similarity(a, b)
        info = {'source_id': a['id'], 'continuation_id': b['id'],
                'source_page': a['page'], 'continuation_page': b['page'],
                'header_similarity': round(similarity, 4)}
        if counts[a['page']] != 1 or counts[b['page']] != 1:
            ambiguous.append({**info, 'reason': 'multiple_tables_on_page'})
        elif similarity >= min_header_similarity:
            edges.append(info)
        else:
            ambiguous.append({**info, 'reason': 'header_not_repeated_or_different'})
    next_id = {e['source_id']: e['continuation_id'] for e in edges}
    incoming = {e['continuation_id'] for e in edges}
    by_id = {t['id']: t for t in ordered}
    groups = []
    for t in ordered:
        if t['id'] in incoming or t['id'] not in next_id:
            continue
        ids = [t['id']]
        while ids[-1] in next_id:
            ids.append(next_id[ids[-1]])
        cells = []
        removed = 0
        for i, table_id in enumerate(ids):
            rows = _rows(by_id[table_id])
            if i and rows and tuple(map(_norm, rows[0])) == _header(t):
                rows = rows[1:]
                removed += 1
            cells.extend(rows)
        groups.append({'id': 'fragment:' + '|'.join(ids), 'table_ids': ids,
                       'pages': [by_id[x]['page'] for x in ids],
                       'columns': t['columns'], 'header': list(t.get('header', [])),
                       'cells': cells, 'rows': len(cells),
                       'repeated_headers_excluded': removed,
                       'confidence_label': 'candidate_repeated_header'})
    return {'groups': groups, 'ambiguous_adjacencies': ambiguous,
            'limitations': 'Only consecutive-page single-table repeated-header candidates; no guarantee of a real continuation. Original tables are retained.'}
