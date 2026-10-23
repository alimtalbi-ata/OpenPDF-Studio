# OpenPDF Studio V50.7 — Qualité, qualification et feuille de route

Auteur : Abdelhalim Talbi — 23 octobre 2026.

## Fonctionnalité livrée
Le moteur de compression automatique compare le reçu RGB V50.6 à une seconde lecture indépendante du PDF source et du candidat : nombre de pages, pixels raster attendus à l'échelle choisie, rotations/cadrages et octets économisés. Une incohérence entraîne un rejet **avant publication**, sans écrasement de la destination. L'API JSON reste compatible avec V50.6 et ajoute `coverage_verification` et `selected_quality.coverage`.

## Tests et preuves
12 tests V50.7 (PDF synthétiques réels à deux pages, page tournée, reçus falsifiés, document chiffré, collision de destination). Régressions V50.6/V50.5/V50.4 en CI Ubuntu et Windows. La compilation, l'installation et la désinstallation Windows doivent être distinguées des tests statiques et validées par les journaux de la CI. Aucune capture Windows simulée.

## Limites
Les pixels ne sont pas re-rendus par la seconde vérification ; elle contrôle **l'exhaustivité déclarée**, non l'exactitude de chaque valeur de qualité. L'audit RGB initial est à échelle bornée et ne certifie ni PDF/A, ni OCR, ni fidélité d'impression, ni accessibilité. Les résultats sur PDF synthétiques ne se généralisent pas à tous les PDF métier.

## Prochaines priorités
1. Corriger les contrats historiques de CI et renforcer la qualification graphique Windows.
2. Élargir le corpus PDF métier : scans, tableaux, liens, formulaires, polices embarquées et gros documents.
3. Étendre les mesures de fidélité des conversions PDF vers Word, Excel et PowerPoint éditables.
