# OpenPDF Studio V18.8 Diagnostic Add-on R36 — Alignement des pages

Auteur : Abdelhalim Talbi

Le rapport HTML rapproche les pages PDF source et cible en utilisant exclusivement les preuves textuelles fournies dans `multipage_audit.exact_text_page_matches` et `candidate_text_page_matches`. Les pages sans correspondance restent séparées ; aucun alignement par numéro n’est inventé. Les candidats sont explicitement marqués à vérifier. Un même numéro de page ne peut être utilisé deux fois.

## Utilisation

1. Produire le diagnostic avec `compare_documents()` et les données d'audit multipage.
2. Exécuter `python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf source.pdf --target-pdf cible.pdf`.
3. Ouvrir `rapport.html` dans un navigateur. Les aperçus réels PDF sont intégrés et les anomalies peuvent pointer vers leur page.

Limite : seules les pages disposant d'un aperçu demandé par une anomalie sont visibles. L'alignement textuel ne garantit ni la fidélité graphique ni l'équivalence des tableaux. Les conversions Office utilisent LibreOffice lorsque demandé explicitement. Pas de qualification Windows native.
