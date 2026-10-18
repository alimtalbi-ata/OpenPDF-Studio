"""Structural and textual fidelity metrics, without claiming semantic/visual equivalence.
Author: Abdelhalim Talbi.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import fitz, json, re

@dataclass(frozen=True)
class StructureMetrics:
    source_pages:int
    candidate_pages:int
    page_delta:int
    source_images:int
    candidate_images:int
    image_delta:int
    source_drawings:int
    candidate_drawings:int
    drawing_delta:int
    source_words:int
    candidate_words:int
    word_recall:float
    compared_pages:int
    warnings:tuple

def _words(document):
    return [w.casefold() for w in re.findall(r"[^\W_]+", " ".join(p.get_text() for p in document),re.UNICODE)]

def compare_structure(source,candidate,*,max_pages=100):
    if not isinstance(max_pages,int) or not 1<=max_pages<=1000: raise ValueError('max_pages invalide')
    if not Path(source).is_file() or not Path(candidate).is_file(): raise FileNotFoundError('PDF absent')
    with fitz.open(source) as a,fitz.open(candidate) as b:
        if a.needs_pass or b.needs_pass: raise ValueError('PDF chiffré')
        if not a.page_count or not b.page_count: raise ValueError('PDF sans pages')
        na=min(a.page_count,max_pages); nb=min(b.page_count,max_pages)
        aa=[a[i] for i in range(na)];bb=[b[i] for i in range(nb)]
        from collections import Counter
        src=Counter(_words(aa));dst=Counter(_words(bb))
        matched=sum(min(n,dst[w]) for w,n in src.items())
        imgs_a=sum(len(p.get_images(full=True)) for p in aa);imgs_b=sum(len(p.get_images(full=True)) for p in bb)
        draw_a=sum(len(p.get_drawings()) for p in aa);draw_b=sum(len(p.get_drawings()) for p in bb)
        warnings=[]
        if a.page_count!=b.page_count:warnings.append('Pagination différente')
        if na<a.page_count or nb<b.page_count:warnings.append('Analyse partielle (max_pages)')
        if imgs_a!=imgs_b:warnings.append('Nombre de références images différent (pas une preuve de perte)')
        if draw_a!=draw_b:warnings.append('Nombre de dessins vectoriels différent (pas une preuve de perte)')
        return StructureMetrics(a.page_count,b.page_count,b.page_count-a.page_count,imgs_a,imgs_b,imgs_b-imgs_a,draw_a,draw_b,draw_b-draw_a,sum(src.values()),sum(dst.values()),round(matched/sum(src.values()),4) if src else 1.0,min(na,nb),tuple(warnings))

def save_metrics(metrics,path):
    path=Path(path);path.write_text(json.dumps(asdict(metrics),ensure_ascii=False,indent=2),encoding='utf-8');return path
