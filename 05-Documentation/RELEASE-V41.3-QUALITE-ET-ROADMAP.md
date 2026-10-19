# OpenPDF Studio V41.3 — Mesure de couverture Office et tests réels
Auteur : Abdelhalim Talbi

## Évolutions
- Normalisation Unicode NFKC avant le calcul de couverture lexicale (variantes pleine largeur, typographie Unicode).
- Tests de préservation textuelle sur fichiers PDF réels vers DOCX, XLSX et PPTX réellement générés.
- Test de multiplicité des mots : une occurrence dans Office ne couvre pas deux occurrences PDF.
- Tests automatiques intégrés à la CI Windows, sans prétention de fidélité géométrique.

## Limites
La couverture textuelle est indicative et ne mesure pas les tableaux, les images, la géométrie ou la qualité d'édition. Aucun résultat manuel Windows n'est revendiqué.

## Roadmap
V41.4 : journal d'audit des opérations avec confidentialité et conservation configurable.
