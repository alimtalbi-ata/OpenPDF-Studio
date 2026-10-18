# R31 — Comparaison des tableaux PDF consolidés

Auteur : Abdelhalim Talbi.

`consolidated_table_compare.compare_consolidated_tables(pdf_tables, office_tables)` fournit un résultat structuré : `matches`, `unmatched_source`, `unmatched_target`, `pdf_fragment_audit`, `pdf_candidate_count` et `limitations`.

La fonction `compare_pdf_office_tables` de `pdf_table_audit.py` expose désormais `consolidated_table_comparison` en plus du diagnostic antérieur. Le résultat est disponible dans `compare_documents(...)['pdf_office_table_audit']['consolidated_table_comparison']` pour PDF↔DOCX/XLSX.

La détection de fragments n'est autorisée que pour des pages consécutives contenant chacune un seul tableau, de même nombre de colonnes et à en-tête suffisamment semblable. Les en-têtes répétés sont exclus du regroupement, sans altérer les tableaux sources. Les différences de lignes sont basées sur un multiensemble de valeurs normalisées. Les changements d'ordre ne sont signalés que si le contenu des lignes est identique.

Limites : la détection PDF dépend de `find_tables()` de PyMuPDF et peut manquer les tableaux sans bordures. Les cellules fusionnées, les formules Excel, la géométrie fine et les tableaux ambigus nécessitent une validation humaine. L'application Windows complète n'est pas comprise.

Tests : `python -m unittest discover -p 'test*.py' -q` puis `for f in test*.js; do node "$f"; done`.
