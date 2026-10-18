# OpenPDF Studio V20.5 — Superposition indicative

Auteur : Abdelhalim Talbi.

## Utilisation
1. Produire un rapport JSON de comparaison puis exporter le diagnostic HTML avec `python diagnostic_dashboard.py rapport.json rapport.html --source-pdf source.pdf --target-pdf cible.pdf`.
2. Ouvrir le rapport HTML localement, choisir une paire de pages appariées.
3. Activer **Superposition des pages appariées**. Ajuster **Opacité cible** (0–100 %).
4. Parcourir les paires avec les boutons de navigation; l'aperçu de superposition suit la paire sélectionnée.

## Précautions
- Fonction active uniquement quand les deux pages PDF ont un aperçu réel et sont appariées.
- La superposition utilise les images de rendu déjà intégrées au HTML, sans appel réseau.
- Aucun recalage géométrique, aucune compensation de rotation, d'échelle ou de marge.
- Un écart visible ne prouve pas une erreur de conversion; une absence d'écart ne prouve pas la fidélité.
- Qualification native Windows et captures réelles non effectuées dans cette livraison.
