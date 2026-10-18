"""R27: conservative text continuity and potential table splits. Author: Abdelhalim Talbi."""
from __future__ import annotations
import re


def _lines(page):
    blocks = page.get('blocks', [])
    if not isinstance(blocks, list):
        raise ValueError('blocks must be a list')
    out=[]
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError('block must be an object')
        text=block.get('text', '')
        if not isinstance(text,str):
            raise ValueError('block text must be a string')
        if text.strip():
            box=block.get('box') or {}
            y=box.get('y') if isinstance(box,dict) else None
            h=box.get('h') if isinstance(box,dict) else None
            out.append((text.strip(), y+h if isinstance(y,(int,float)) and isinstance(h,(int,float)) else None))
    return out


def _row_shape(text):
    # Only a candidate: text-only detection cannot establish table structure.
    return bool(re.search(r'\t|\s{3,}|\s[|]\s|[|]\s',text))


def audit_page_boundaries(pages):
    """Flag probable continuations; never assert confirmed split tables."""
    if not isinstance(pages,list) or len(pages)>1000:
        raise ValueError('pages must be a list of at most 1000 pages')
    boundaries=[]
    for index in range(len(pages)-1):
        first,second=pages[index],pages[index+1]
        a,b=_lines(first),_lines(second)
        if not a or not b:continue
        last=a[-1][0]; opening=b[0][0]
        # Prose continuation across pages (hyphen or unfinished sentence).
        hyphenated=last.endswith(('-', '‐', '‑')) and opening[:1].islower()
        unfinished=bool(re.search(r'[a-zà-ÿ,;:]$',last,re.I)) and opening[:1].islower()
        table_candidate=_row_shape(last) and _row_shape(opening)
        if hyphenated or unfinished or table_candidate:
            reasons=[]
            if hyphenated:reasons.append('hyphenated_word_continuation')
            if unfinished:reasons.append('possible_paragraph_continuation')
            if table_candidate:reasons.append('possible_table_row_continuation')
            boundaries.append({'after_page':index+1,'before_page':index+2,
                               'reasons':reasons,'status':'candidate_only',
                               'last_text_excerpt':last[:100],
                               'next_text_excerpt':opening[:100]})
    return {'page_count':len(pages),'boundary_candidates':boundaries,
            'warnings':['Heuristic text-only indicators; not verified table segmentation or visual layout',
                        'Table candidates can include multi-column prose or aligned text']}
