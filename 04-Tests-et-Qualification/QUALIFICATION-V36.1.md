# OpenPDF Studio V36.1 — Audit de dépendances et build canonique

Auteur : Abdelhalim Talbi

## Mesures vérifiées
- Modules Python trouvés : 499
- Modules analysés par AST : 499
- Modules atteignables par imports statiques depuis l'ancien point d'entrée : 29
- Modules UI versionnés atteignables : 4
- Tests V36.1 : 5/5 PASS sous Linux.

## Corrections
- Nouveau point d'entrée stable `openpdf_studio.py` ; conservation temporaire de l'implémentation historique pour éviter une rupture.
- Script de build synchronisé V36.1, fichier Inno Setup V36.1, vérificateur statique V36.1.
- Graphe complet dans `ARCHITECTURE-IMPORTS-V36.1.json`.

## Limites
- Analyse statique : imports dynamiques non couverts ; aucune suppression de code sur cette seule base.
- Le build Windows n'a pas été exécuté. La compilation et le lancement réel doivent être qualifiés sur Windows.
- Le script Windows conserve des prérequis réseau et un ensemble limité de tests avant packaging ; il n'est pas encore une preuve de fonctionnement complet.
