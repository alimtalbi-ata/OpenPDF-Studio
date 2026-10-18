"""Conservative page sequence diagnostics. Author: Abdelhalim Talbi."""
from __future__ import annotations
from difflib import SequenceMatcher
from pathlib import Path
import hashlib
import fitz

MAX_PAGES = 500
MAX_CHARS = 20000

def _pages(path):
    with fitz.open(path) as pdf:
        if pdf.page_count > MAX_PAGES:
            raise ValueError("PDF exceeds page audit limit")
        result = []
        for page in pdf:
            text = " ".join(page.get_text("text").split())[:MAX_CHARS]
            result.append({"text": text, "digest": hashlib.sha256(text.encode()).hexdigest(),
                           "width": round(page.rect.width, 2), "height": round(page.rect.height, 2)})
        return result

def audit_page_sequence(source, target):
    """Exact normalized-text matches only; no inference of page equivalence."""
    a, b = _pages(source), _pages(target)
    unmatched_a = set(range(len(a)))
    unmatched_b = set(range(len(b)))
    pairs = []
    for i, page in enumerate(a):
        if not page["text"]:
            continue
        matches = [j for j in sorted(unmatched_b) if b[j]["text"] and b[j]["digest"] == page["digest"]]
        if matches:
            j = min(matches, key=lambda k: (abs(k-i), k))
            unmatched_a.remove(i); unmatched_b.remove(j)
            pairs.append({"source_page": i+1, "target_page": j+1,
                          "moved": i != j, "method": "exact_normalized_text"})
    geometry = [{"source_page": p["source_page"], "target_page": p["target_page"],
                 "source_size": [a[p["source_page"]-1]["width"], a[p["source_page"]-1]["height"]],
                 "target_size": [b[p["target_page"]-1]["width"], b[p["target_page"]-1]["height"]]}
                for p in pairs if (a[p["source_page"]-1]["width"], a[p["source_page"]-1]["height"]) !=
                                 (b[p["target_page"]-1]["width"], b[p["target_page"]-1]["height"])]
    return {"method": "exact_normalized_text_only", "source_pages": len(a), "target_pages": len(b),
            "matched_pages": sorted(pairs, key=lambda p: p["source_page"]),
            "moved_pages": [p for p in pairs if p["moved"]],
            "unmatched_source_pages": [i+1 for i in sorted(unmatched_a)],
            "unmatched_target_pages": [j+1 for j in sorted(unmatched_b)],
            "empty_text_source_pages": [i+1 for i,p in enumerate(a) if not p["text"]],
            "empty_text_target_pages": [j+1 for j,p in enumerate(b) if not p["text"]],
            "geometry_changes_on_exact_matches": geometry,
            "limitations": ["Text matches do not prove visual equivalence", "Unmatched pages may be modified, inserted or deleted", "No OCR or semantic matching"]}
