# OpenPDF Studio V43.7 — Cohérence de l'aperçu asynchrone
Auteur : Abdelhalim Talbi

## Correction
La sélection des bornes d'extraction depuis l'aperçu est désormais bloquée tant que l'image de la page n'a pas été chargée pour le document actif. L'ancien nombre de pages et l'identité du document précédemment affiché sont invalidés dès le début d'une nouvelle demande d'aperçu.

- État explicite _preview_loaded_source, distinct du document demandé.
- Réinitialisation du nombre de pages pendant le chargement.
- Publication de l'identité chargée uniquement après un rendu réussi.
- Trois tests de régression sur l'invalidation et la validation des pages.

## Limites
La recette GUI manuelle Windows reste nécessaire pour les aspects de rendu et de navigation à différents DPI.
