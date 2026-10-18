# R29 — Audit des tableaux PDF / Office

Auteur : Abdelhalim Talbi.

`pdf_table_audit.py` utilise `page.find_tables()` de PyMuPDF pour identifier des tableaux PDF et `table_structure_audit.py` pour lire les tableaux natifs DOCX et les tableaux nommés XLSX.

```python
from pdf_table_audit import compare_pdf_office_tables
report = compare_pdf_office_tables('source.pdf', 'converti.docx', threshold=0.55)
print(report['matches'], report['unmatched_source'])
```

La fonction `compare_documents('source.pdf', 'converti.docx')` ajoute automatiquement la clé `pdf_office_table_audit` au diagnostic. La similarité combine contenu des cellules (75 %), en-tête (15 %) et nombre de colonnes (10 %). Chaque tableau n'est apparié qu'une fois. Les cellules manquantes et ajoutées sont signalées dans les correspondances.

**Limites :** les PDF n'ont souvent pas de structure tabulaire explicite ; `find_tables()` peut manquer un tableau sans bordures ou identifier un faux positif. La reconnaissance ne fait pas d'OCR. Les cellules fusionnées, les tableaux scindés sur plusieurs pages et les tableaux Excel non nommés ne sont pas entièrement pris en charge. Les absences signalées sont des candidates à réviser, non des pertes prouvées. Aucun essai natif Windows n'a été effectué.
