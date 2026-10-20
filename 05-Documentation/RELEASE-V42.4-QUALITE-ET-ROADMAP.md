# OpenPDF Studio V42.4 — Géométrie et occurrences des images
Auteur : Abdelhalim Talbi

## Anomalie métier
La V42.3 compare les images décodées par page, mais pas leurs positions : déplacer une image sans modifier ses pixels pouvait échapper au contrôle. De même, une ressource image peut être placée plusieurs fois sur une page.

## Correctif
- Pour chaque occurrence d'image, comparer pixels décodés, dimensions, rectangle et transformation affine.
- Comparaison multiensemble par page, y compris répétitions d'une ressource image.
- Tolérance géométrique de 5 décimales pour limiter les faux positifs numériques.
- Tests PDF réels : optimisation inchangée acceptée, déplacement rejeté, occurrence supplémentaire rejetée.

## Limites
Ne constitue pas une preuve d'identité de rendu complet : masques, calques, transparences, annotations, vectoriels et espaces colorimétriques complexes demandent des tests de rendu dédiés. Qualification interactive Windows et captures réelles non revendiquées.
