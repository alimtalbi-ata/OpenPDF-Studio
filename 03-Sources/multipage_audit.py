"""Conservative multipage quality audit for OpenPDF Studio. Author: Abdelhalim Talbi."""
from __future__ import annotations
from difflib import SequenceMatcher
from collections import Counter
import re


def _tokens(page):
    return re.findall(r'\w+', ' '.join(str(b.get('text', '')) for b in page.get('blocks', [])), re.UNICODE | re.IGNORECASE)


def _similarity(a, b):
    x, y = Counter(w.casefold() for w in _tokens(a)), Counter(w.casefold() for w in _tokens(b))
    total = sum(x.values()) + sum(y.values())
    return (2 * sum((x & y).values()) / total) if total else 1.0


def detect_split_merge_candidates(source_pages, target_pages, *, threshold=0.82, margin=0.12):
    """Suggest 1:2 and 2:1 text reflow; never claim verified page equivalence.

    Uses token-multiset Dice overlap, excludes empty pages, requires both
    constituent pages to contribute, and flags competing candidate matches.
    """
    if not 0 < threshold <= 1 or not 0 <= margin < 1:
        raise ValueError('Invalid split/merge thresholds')
    if len(source_pages) > 1000 or len(target_pages) > 1000:
        raise ValueError('Maximum 1000 pages per document')
    def bag(page): return Counter(w.casefold() for w in _tokens(page))
    a=[bag(p) for p in source_pages];b=[bag(p) for p in target_pages]
    def dice(x,y):
        den=sum(x.values())+sum(y.values())
        return 2*sum((x&y).values())/den if den else 0.0
    out=[]
    for kind,left,right in [('split',a,b),('merge',b,a)]:
        for i,original in enumerate(left):
            if not original:continue
            candidates=[]
            for j in range(len(right)-1):
                first,second=right[j],right[j+1]
                if not first or not second:continue
                combined=first+second
                score=dice(original,combined)
                contribution1=sum((original&first).values())/sum(original.values())
                contribution2=sum((original&second).values())/sum(original.values())
                if score>=threshold and min(contribution1,contribution2)>=0.08:
                    candidates.append((score,j))
            candidates.sort(reverse=True)
            if not candidates:continue
            best,j=candidates[0]
            ambiguous=len(candidates)>1 and best-candidates[1][0]<margin
            out.append({'type':kind,'source_pages':[i+1] if kind=='split' else [j+1,j+2],
                        'target_pages':[j+1,j+2] if kind=='split' else [i+1],
                        'text_overlap':round(best,4),'status':'ambiguous_candidate' if ambiguous else 'candidate_only'})
    return out


def audit_multipage(source_pages, target_pages, *, match_threshold=0.55):
    """Diagnose pagination changes using monotone matching; no invented visual fidelity."""
    if not isinstance(source_pages, list) or not isinstance(target_pages, list):
        raise ValueError('Pages must be lists')
    if len(source_pages) > 1000 or len(target_pages) > 1000:
        raise ValueError('Maximum 1000 pages per document')
    if not 0 < match_threshold <= 1:
        raise ValueError('match_threshold must be within (0,1]')
    src = [_tokens(p) for p in source_pages]
    dst = [_tokens(p) for p in target_pages]
    # Monotone page matching avoids misleading index-only comparison after inserted pages.
    signatures = [' '.join(t[:120]) for t in src], [' '.join(t[:120]) for t in dst]
    matches = SequenceMatcher(None, *signatures, autojunk=False).get_matching_blocks()
    exact = [(i + k, j + k) for i, j, n in matches for k in range(n)]
    paired_src = {i for i, _ in exact}
    paired_dst = {j for _, j in exact}
    # Conservative similarity suggestions for unpaired pages, preserving order.
    suggestions = []
    remaining_src = [i for i in range(len(src)) if i not in paired_src]
    remaining_dst = [j for j in range(len(dst)) if j not in paired_dst]
    for i in remaining_src:
        candidates = [(j, _similarity(source_pages[i], target_pages[j])) for j in remaining_dst]
        if candidates:
            j, score = max(candidates, key=lambda v: v[1])
            if score >= match_threshold:
                suggestions.append({'source_page': i + 1, 'target_page': j + 1, 'text_overlap': round(score, 4), 'status': 'candidate_only'})
                remaining_dst.remove(j)
    empty_src = [i + 1 for i, t in enumerate(src) if not t]
    empty_dst = [j + 1 for j, t in enumerate(dst) if not t]
    return {
        'source_pages': len(src), 'target_pages': len(dst),
        'page_count_delta': len(dst) - len(src),
        'exact_text_page_matches': [{'source_page': i + 1, 'target_page': j + 1} for i, j in exact],
        'candidate_text_page_matches': suggestions,
        'unmatched_source_pages': [i + 1 for i in remaining_src],
        'unmatched_target_pages': [j + 1 for j in remaining_dst],
        'empty_text_source_pages': empty_src, 'empty_text_target_pages': empty_dst,
        'split_merge_candidates': detect_split_merge_candidates(source_pages,target_pages),
        'warnings': ['Text-only page alignment: images, diagrams, table structure, typography and glyph rendering are not validated',
                     'Pagination changes can split or merge text; candidates are not proof of equivalence'],
    }
