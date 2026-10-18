"""Compare conservatively consolidated PDF table fragments with native Office tables.

Author: Abdelhalim Talbi. Candidate-only, never a claim of exact fidelity.
"""
from collections import Counter
from pdf_table_audit import match_tables
from table_fragment_audit import audit_pdf_table_fragments


def _norm(x):
    return ' '.join(str(x or '').casefold().split())


def _tokens(t):
    return Counter(_norm(c) for row in t['cells'] for c in row if _norm(c))


def compare_consolidated_tables(pdf_tables, office_tables, *, threshold=.55):
    """Compare grouped fragments and ungrouped tables without double counting.

    Only PDF fragments with repeated headers on adjacent single-table pages
    are grouped. Original IDs and pages are retained as provenance.
    """
    fragments = audit_pdf_table_fragments(pdf_tables)
    grouped_ids = {id_ for g in fragments['groups'] for id_ in g['table_ids']}
    candidates = [*fragments['groups'], *(t for t in pdf_tables if t['id'] not in grouped_ids)]
    comparison = match_tables(candidates, office_tables, threshold=threshold)
    by_pdf = {t['id']: t for t in candidates}
    by_office = {t['id']: t for t in office_tables}
    enriched = []
    for m in comparison['matches']:
        a, b = by_pdf[m['source_id']], by_office[m['target_id']]
        src_rows = a.get('cells', [])
        tgt_rows = b.get('cells', [])
        # Multiset differences cannot establish which row moved. Only flag candidates.
        src_row_counts = Counter(tuple(_norm(c) for c in row) for row in src_rows)
        tgt_row_counts = Counter(tuple(_norm(c) for c in row) for row in tgt_rows)
        missing_rows = list((src_row_counts - tgt_row_counts).elements())[:100]
        added_rows = list((tgt_row_counts - src_row_counts).elements())[:100]
        src_order = [tuple(_norm(c) for c in row) for row in src_rows]
        tgt_order = [tuple(_norm(c) for c in row) for row in tgt_rows]
        order_changed = not missing_rows and not added_rows and src_order != tgt_order
        enriched.append({**m, 'source_pages': a.get('pages', [a.get('page')]),
                         'source_table_ids': a.get('table_ids', [a['id']]),
                         'missing_rows': [list(row) for row in missing_rows],
                         'added_rows': [list(row) for row in added_rows],
                         'row_order_changed_candidate': order_changed,
                         'repeated_headers_excluded': a.get('repeated_headers_excluded', 0)})
    return {**comparison, 'matches': enriched,
            'pdf_fragment_audit': fragments,
            'pdf_candidate_count': len(candidates),
            'limitations': 'Heuristic extraction, conservative grouping and token matching. Row order changes are candidates, not proof of data movement; merged cells require manual review.'}
