# OpenPDF Studio V23.5 — Audit de mise en page

```python
from layout_table_audit_v235 import audit_layout_tables
result = audit_layout_tables("source.pdf", "cible.pdf", tolerance=2.0)
```

Pour intégrer au dashboard, fournir `report["layout_table_audit_v235"] = result`. Seules les pages avec texte normalisé strictement identique sont comparées. Les changements sont des indices nécessitant une revue humaine. Aucune qualification native Windows réalisée.

Auteur : Abdelhalim Talbi.
