# OpenPDF Studio V21.4 — Diagnostic géométrique vérifiable

Auteur : Abdelhalim Talbi

## Utilisation

Le rapport JSON peut contenir `visual_regions_raster_space` (liste de régions explicites) et `page_annotations` (rectangles texte en points PDF). Chaque région raster doit spécifier `side`, `page`, `coordinate_space: full_page_raster`, `rotation: 0`, `raster_width`, `raster_height`, `pdf_width`, `pdf_height` et `bbox: [x0,y0,x1,y1]`.

Le pipeline V21.4 vérifie les coordonnées, rejette les doublons, limite le volume analysé et produit les corrélations IoU des régions effectivement localisées. Le rapport HTML présente le nombre de régions acceptées et de rejets.

Exemple : `python diagnostic_dashboard.py --help` pour consulter les options CLI.

**Limites** : aucune conversion implicite des pixels d'une superposition navigateur ; rotations/recadrages non supportés ; aucune classification sémantique ; corrélations candidates, à contrôler humainement. La qualification Windows native et les captures d'interface réelles ne sont pas disponibles dans cette livraison.
