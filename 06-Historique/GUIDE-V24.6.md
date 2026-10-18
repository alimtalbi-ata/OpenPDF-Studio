# OpenPDF Studio V24.6 — mise en évidence des régions

Auteur : Abdelhalim Talbi.

Dans la navigation des comparaisons, utiliser **Source** ou **Cible** pour sélectionner une région géométrique validée. La région active reçoit un contour orange renforcé et un statut lisible par lecteur d’écran. La fiche de preuve conserve les coordonnées PDF vérifiées. Le changement de page et l’effacement de sélection suppriment le contour précédent.

Le statut indique l’appariement de pages, sans inférer une correspondance entre régions. Les pages non appariées restent consultables séparément. Les régions sans provenance `raster-mapping-validated` ne sont pas mises en évidence.

**Limites :** module de diagnostic HTML autonome, pas une application Windows native ; les captures Chromium Linux ne constituent pas une qualification Windows.
