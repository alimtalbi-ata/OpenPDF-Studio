# V529 — Audit des cellules fantômes PDF → Excel

**Auteur : Abdelhalim Talbi** · **Application : V51.4** · **24 octobre 2026**

## Défaut reproduit
Pour un PDF à deux colonnes, la feuille XLSX utilise quatre colonnes (A:D) car A1:D1 stocke la provenance. L'audit `verify_xlsx_tables` vérifiait seulement les colonnes du tableau (A:B) dans les lignes de données, et ignorait la ligne 2. Une valeur arbitraire en C4, D3 ou A2 pouvait donc passer la vérification. Une feuille masquée passait aussi.

## Correctif
- Refuser toute valeur non vide dans la ligne 2 des feuilles de tableaux.
- Refuser toute valeur hors grille dans les colonnes réservées aux métadonnées.
- Refuser les feuilles de tableaux masquées.
- Conserver le comportement historique hors mode `table_mode=True`.

## Qualification
- **Avant correctif :** 5 échecs sur 6 tests V529 ; les mutations ne déclenchaient pas d'erreur.
- **Après correctif :** 6/6 V529 PASS, 132/132 tests XLSX Linux PASS.
- **Données :** PDF synthétiques réellement générés et convertis en classeurs XLSX ; aucune annotation humaine.
- **CI :** matrice Ubuntu/Windows et Windows native, à vérifier sur le commit final.
- **Limites :** exactitude de l'extraction de PyMuPDF seulement ; ni fidélité sémantique métier ni fidélité visuelle prouvée.
- **Windows :** ne pas confondre réussite de compilation native et validation graphique humaine. Les binaires V528 ne contiennent pas V529.

## Chaîne de validation
PDF source → extraction PyMuPDF → classeur XLSX éditable → audit de provenance, grille et cellules hors-grille → contrôle OOXML et publication atomique.

**Sécurité :** aucune fusion automatique, aucun secret, `main` préservée.
