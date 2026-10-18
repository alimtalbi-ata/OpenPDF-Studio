"""Bounded, conservative layout/table audit. Author: Abdelhalim Talbi."""
from __future__ import annotations
import fitz
from page_sequence_audit_v234 import audit_page_sequence

MAX_BLOCKS = 1000

def _blocks(page):
    blocks = []
    for item in page.get_text("blocks"):
        if len(blocks) >= MAX_BLOCKS:
            raise ValueError("Text block limit exceeded")
        text = " ".join(str(item[4]).split())
        if text:
            blocks.append({"text": text, "rect": tuple(round(float(x), 2) for x in item[:4])})
    return blocks

def _tables(page):
    if not hasattr(page, "find_tables"):
        return {"count": None, "warning": "Table detection unavailable"}
    try:
        found = page.find_tables()
        return {"count": len(found.tables), "warning": None}
    except Exception as exc:
        return {"count": None, "warning": "Table detection failed: " + type(exc).__name__}

def audit_layout_tables(source, target, *, tolerance=2.0):
    """Compare exact-text-matched pages only. Geometric differences are review candidates."""
    if not 0 <= tolerance <= 100:
        raise ValueError("tolerance must be between 0 and 100 points")
    sequence = audit_page_sequence(source, target)
    findings = []
    with fitz.open(source) as left, fitz.open(target) as right:
        for pair in sequence["matched_pages"]:
            a, b = pair["source_page"], pair["target_page"]
            source_blocks, target_blocks = _blocks(left[a-1]), _blocks(right[b-1])
            if len(source_blocks) != len(target_blocks):
                findings.append({"kind": "text_block_count", "source_page": a, "target_page": b,
                                 "source_count": len(source_blocks), "target_count": len(target_blocks)})
            elif [x["text"] for x in source_blocks] == [x["text"] for x in target_blocks]:
                moved = sum(1 for x,y in zip(source_blocks,target_blocks)
                            if any(abs(v-w)>tolerance for v,w in zip(x["rect"],y["rect"])))
                if moved:
                    findings.append({"kind": "text_block_geometry", "source_page": a,
                                     "target_page": b, "affected_blocks": moved, "regions": [
                                         {"source_bbox": x["rect"], "target_bbox": y["rect"], "text_excerpt": x["text"][:100]}
                                         for x,y in zip(source_blocks,target_blocks)
                                         if any(abs(v-w)>tolerance for v,w in zip(x["rect"],y["rect"]))][:100]})
            else:
                findings.append({"kind": "text_block_order", "source_page": a, "target_page": b})
            st, tt = _tables(left[a-1]), _tables(right[b-1])
            if st["count"] is not None and tt["count"] is not None and st["count"] != tt["count"]:
                findings.append({"kind": "table_count_candidate", "source_page": a,
                                 "target_page": b, "source_count": st["count"], "target_count": tt["count"]})
    return {"method": "exact_text_matched_pages_geometry_heuristic", "tolerance_points": tolerance,
            "matched_pages_examined": len(sequence["matched_pages"]), "findings": findings,
            "unmatched_source_pages": sequence["unmatched_source_pages"],
            "unmatched_target_pages": sequence["unmatched_target_pages"],
            "limitations": ["Text equality does not prove visual equivalence", "Table detection is heuristic", "Unmatched pages are not geometrically compared", "No OCR"]}
