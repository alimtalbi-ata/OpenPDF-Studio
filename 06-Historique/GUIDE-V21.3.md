# OpenPDF Studio V21.3 — Conversion contrôlée des coordonnées

Auteur : Abdelhalim Talbi

La V21.3 introduit `visual_coordinate_transform.py`, qui transforme les rectangles raster en coordonnées PDF uniquement lorsque les dimensions et la provenance sont explicites.

Entrée JSON facultative : `visual_regions_raster_space`, liste d’objets comportant `side`, `page`, `coordinate_space: full_page_raster`, `rotation: 0`, `raster_width`, `raster_height`, `pdf_width`, `pdf_height`, `bbox: [x0,y0,x1,y1]`. Les coordonnées raster doivent être celles de la page complète non recadrée, et non du canvas ou de la fenêtre navigateur.

La transformation utilise `x_pdf=x_raster*pdf_width/raster_width`, `y_pdf=y_raster*pdf_height/raster_height`. Les régions converties sont soumises à la corrélation spatiale existante avec les annotations de texte. Les données absentes, non finies, hors bornes, recadrées ou tournées sont refusées. Aucun appariement implicite des masques du navigateur.

Exécution : `python -m unittest discover -p 'test*.py'`. Cette archive est un add-on, pas une application Windows complète. Les captures réelles et tests Windows restent indisponibles.
