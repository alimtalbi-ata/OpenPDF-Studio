# OpenPDF Studio V21.2 — Corrélation spatiale contrôlée

Auteur : Abdelhalim Talbi.

Le rapport HTML présente une section « Corrélation texte / régions visuelles ».

Le JSON peut fournir `visual_regions_pdf_space` : liste d’objets `{side, page, bbox}` où `bbox=[x0,y0,x1,y1]` en **coordonnées PDF réelles**, et `page_annotations` de même structure. Seules les intersections sur la même page et le même côté sont signalées, avec IoU. Aucun appariement automatique des coordonnées réduites du navigateur n'est effectué ; les régions calculées dans le navigateur ne sont donc pas utilisées ici sans transformation explicitement vérifiée. Aucune preuve de causalité ou de fidélité ne peut être déduite du chevauchement.

Tests : `python -m unittest discover -p 'test*.py'` puis `for f in test*.js; do node "$f"; done`.

Windows : aucune recette native ni capture d'interface réelle dans cet environnement. `CAPTURES-STATUS.md` documente cette limite.
