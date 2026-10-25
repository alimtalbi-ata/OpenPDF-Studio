# OpenPDF Studio V43.6 — Sélection des bornes d'extraction depuis l'aperçu
Auteur : Abdelhalim Talbi

## Parcours utilisateur
Lorsqu'« Extraire » est sélectionné, deux boutons permettent de reprendre la page actuellement affichée dans l'aperçu comme début ou fin de la plage d'extraction.

- « Début = page affichée » et « Fin = page affichée ».
- Les boutons sont visibles uniquement en extraction.
- Protection contre les aperçus absents, obsolètes ou appartenant à un autre document.
- Six tests de logique : première et dernière pages, source différente, aperçu non chargé, hors limites, aucune sélection.
- Validation de plage V43.5 conservée avant exécution.

## Limites
Les tests automatisés valident le comportement du code, pas une recette visuelle interactive de l'interface Windows.
