# OpenPDF Studio V25.2 — Export de preuve de région

Auteur : Abdelhalim Talbi.

Sélectionner une région raster vérifiée sur la page active. Le bouton **Exporter la preuve de région JSON** devient actif uniquement après validation de la région et de ses coordonnées PDF. L’export contient côté du document, numéro de page, indice, boîte PDF en points, provenance et statut d’appariement des pages. Le champ `region_cross_document_match` reste `not_asserted` : aucune identité entre régions n’est déduite. Toute navigation ou réinitialisation invalide la sélection exportable.

Qualification navigateur Chromium Linux sur PDF synthétiques ; aucune qualification native Windows. Module de diagnostic, pas suite PDF Windows complète.
