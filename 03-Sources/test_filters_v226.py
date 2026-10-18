from pathlib import Path
ROOT=Path(__file__).parent
def test_contextual_csv():
 s=(ROOT/'viewer.js').read_text();assert "'sourcePage','targetPage'" in s;assert "report.pages[r.pageIndex]?.sourcePage" in s
def test_export_counts():
 s=(ROOT/'viewer.js').read_text();assert 'exportedCount:records.length' in s;assert 'filteredCount:records.length' in s
def test_session_filters():
 s=(ROOT/'viewer.js').read_text();assert 'const oldPage=page.value,oldCategory=category.value' in s;assert "$('pageFilter').onchange=render" in s
def test_version():
 s=(ROOT/'viewer.js').read_text();assert 'diagnostic-v22.6.json' in s;assert 'anomalies-filtrees-v22.6.csv' in s
