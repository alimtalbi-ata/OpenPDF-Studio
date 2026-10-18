# OpenPDF Studio V21.1 — Analyse morphologique des zones

Auteur : Abdelhalim Talbi

Dans le rapport HTML, activez la superposition de deux pages disponibles, puis cliquez sur « Visualiser les écarts après recalage ». Les cinq premières régions affichent désormais leur forme géométrique indicative (bande horizontale, verticale, zone compacte/mixte) et la proportion de cellules occupées.

**Important :** aucune déduction automatique de changement de texte, police ou déplacement d’objet. Les régions proviennent d’une carte de luminance réduite ; leur forme n'est pas une classification sémantique.

## Tests

`python -m unittest discover -p 'test*.py'` puis `node test_regions_v211.js`.

## Portée

Add-on de diagnostic uniquement. Ni validation native Windows, ni captures d'écran réelles. Voir `CAPTURES-STATUS.md`.
