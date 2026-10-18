# OpenPDF Studio V24.7 — Guide utilisateur

Auteur : Abdelhalim Talbi.

Dans le tableau de bord de diagnostic, activer **Afficher les régions vérifiées** puis utiliser **Source** ou **Cible** pour sélectionner les régions mesurées de chaque document. L’option **Centrer automatiquement la région sélectionnée** est activée par défaut et peut être désactivée à tout moment. Le centrage utilise la zone défilable du document sélectionné, et jamais les coordonnées d’un autre document.

Les régions doivent provenir de `visual_regions_raster_space` avec transformation validée. Aucun appariement entre régions source/cible n’est inféré. Les pages non appariées restent indépendantes. Les preuves et les coordonnées sont des diagnostics indicatifs soumis à revue humaine.

La capture intégrée est effectuée avec Chromium Linux headless et des PDF synthétiques réels ; **aucune qualification Windows native** n’est revendiquée. Ce livrable est un add-on de diagnostic, pas une application Windows native complète.
