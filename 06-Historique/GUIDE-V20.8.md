# OpenPDF Studio V20.8 — guide du diagnostic

Auteur : Abdelhalim Talbi.

Ouvrir le rapport HTML produit par `diagnostic_dashboard.py`, activer la superposition sur une paire de pages disposant de deux aperçus, puis régler l’opacité, les décalages X/Y et **l’échelle cible (90–110 %)**. Le bouton « Proposer un recalage automatique » cherche un décalage et une échelle approximatifs par comparaison locale des contours. Aucun résultat n’est certifié : inspecter manuellement les pages, les textes et les tableaux. « Réinitialiser » remet les décalages à zéro et l’échelle à 100 %.

Le moteur de recalage est une heuristique basée sur une grille 128×128. Il peut échouer sur les documents peu contrastés, déformés, recadrés, ou à pagination différente. Il n'effectue aucune conversion Office et n'envoie pas de données sur le réseau. La qualification Windows native et les captures réelles de l’application complète restent indisponibles.
