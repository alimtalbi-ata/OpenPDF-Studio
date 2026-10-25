# OpenPDF Studio V42.3 — Intégrité des images par page
Auteur : Abdelhalim Talbi

## Anomalie identifiée
La V42.2 comparait un multiensemble global des images. Deux PDF pouvaient donc posséder les mêmes images, mais déplacées d'une page à une autre, et être considérés à tort comme équivalents.

## Correctif
- Empreintes des images décodées comparées page par page.
- Refus explicite dès la première page dont les images diffèrent.
- Conservation des contrôles de cardinalité, texte et publication exclusive.
- Tests PDF réels : optimisation sans changement acceptée, images permutées entre pages rejetées.

## Limites
Cette vérification ne garantit pas les coordonnées de placement ni le rendu complet des pages. Les masques, annotations, transformations et éléments vectoriels demandent une qualification visuelle dédiée. Aucun résultat de recette interactive Windows ni capture réelle n'est inventé.
