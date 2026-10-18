from pathlib import Path

ROOT = Path(__file__).parent

def test_page_summary_panel_is_present():
    html = (ROOT / "viewer.html").read_text(encoding="utf-8")
    js = (ROOT / "viewer.js").read_text(encoding="utf-8")
    assert 'id="pageSummary"' in html
    assert "diagnosticCenter.records.filter(x=>x.pageIndex===index)" in js
    assert "Aucune anomalie enregistrée dans le centre de diagnostic" in js

def test_page_summary_uses_current_page_metrics():
    js = (ROOT / "viewer.js").read_text(encoding="utf-8")
    assert "p.missing.length" in js and "p.added.length" in js and "p.moves.length" in js
    assert "quality.pages[index].pageScore" in js
