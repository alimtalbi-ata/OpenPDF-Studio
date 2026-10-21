"""V43.9 PDF link and annotation preservation. Author: Abdelhalim Talbi."""
import fitz

def _page_snapshot(page):
    links = tuple(sorted((str(x.get("uri", "")), x.get("kind"), x.get("page"), str(x.get("from"))) for x in page.get_links()))
    annotations = tuple(sorted((a.type[0], str(a.rect), a.info.get("content", "")) for a in (page.annots() or ())))
    return links, annotations

def validate_structure_preserved(source, candidate):
    with fitz.open(source) as left, fitz.open(candidate) as right:
        if left.page_count != right.page_count:
            raise RuntimeError("Nombre de pages modifié")
        for index in range(left.page_count):
            if _page_snapshot(left[index]) != _page_snapshot(right[index]):
                raise RuntimeError("Liens ou annotations PDF modifiés")
    return {"pages_verified": left.page_count}
