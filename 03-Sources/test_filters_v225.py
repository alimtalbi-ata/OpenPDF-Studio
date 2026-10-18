from pathlib import Path
ROOT=Path(__file__).parent
def test_filter_controls_exist():
    html=(ROOT/'viewer.html').read_text(encoding='utf-8')
    assert 'id="pageFilter"' in html and 'id="categoryFilter"' in html and 'id="exportCsv"' in html
def test_filters_combine_and_exports_are_scoped():
    js=(ROOT/'viewer.js').read_text(encoding='utf-8')
    assert "function filteredRecords()" in js
    assert "x.pageIndex===Number($('pageFilter').value)" in js
    assert "String(x.category||'Non catégorisée')===$('categoryFilter').value" in js
    assert "records,report,quality" in js and "records.map(r=>fields.map" in js
def test_empty_filter_is_not_a_fidelity_claim():
    guide=(ROOT/'GUIDE-V22.5.md').read_text(encoding='utf-8')
    assert 'non que le document est certifié fidèle' in guide
