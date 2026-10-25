# OpenPDF Studio V42.6 — Géométrie des pages PDF
Auteur : Abdelhalim Talbi

## Diagnostic
Le contrôle de rendu V42.5 compare les pixels basse résolution, mais une modification des boîtes de page PDF ou de leur rotation doit être détectée indépendamment du contenu visible.

## Développement
- Comparaison MediaBox, CropBox et rotation par page avant le rendu.
- Rejet avant publication en cas de modification de la géométrie PDF.
- Trois tests de régression : géométrie identique, rotation changée, zone de recadrage modifiée.
- Préservation des contrôles précédents de texte, images, placements et rendu.

## Qualification et limites
Le workflow Windows exécute les tests et compile les binaires. Aucune qualification interactive Windows n'est prétendue ; les captures réelles restent à produire. Le contrôle basse résolution n'est pas une garantie absolue de fidélité graphique.
