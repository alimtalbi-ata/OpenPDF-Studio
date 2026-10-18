# OpenPDF Studio V20.7 — Proposition de recalage automatique

Dans le rapport HTML, activer la superposition sur une paire de pages PDF. Cliquer sur « Proposer un recalage automatique ». Le navigateur compare localement les contours des deux aperçus, recherche une translation limitée et applique une proposition uniquement si la réduction relative de l’écart dépasse 8 %. Sinon aucun décalage n’est appliqué. Les réglages X/Y manuels et le bouton de réinitialisation restent disponibles.

**Limites** : méthode heuristique fondée sur les contours de rendus réduits à 128×128, pas de rotation, pas de déformation ni de correction d’échelle ; une page peu contrastée est refusée. Le pourcentage affiché est un gain de score, pas une probabilité de justesse. Une vérification humaine reste indispensable. Aucune donnée envoyée sur le réseau.

Ce paquet est un add-on de diagnostic et non l’application Windows native complète. Tests natifs Windows et captures réelles de l’application non réalisés.

Auteur : Abdelhalim Talbi.
