# OpenPDF Studio V42.5 — Contrôle de rendu visuel
Auteur : Abdelhalim Talbi

## Constat
Les contrôles de texte et d'images incorporées ne détectent pas nécessairement les modifications des éléments vectoriels et de la composition graphique.

## Implémentation
- Rendu de chaque page source et candidate avec PyMuPDF en RGB à échelle 0,5.
- Empreinte SHA-256 des pixels et comparaison stricte des dimensions, canaux et données.
- Rejet du candidat avant publication si une page diffère.
- Contrôle borné à 12 millions de pixels par page ; rejet explicite si la limite est dépassée, sans saut silencieux.
- Intégration aux profils de compression sans perte uniquement.
- Tests réels : optimisation inchangée acceptée ; modification vectorielle sans modification textuelle rejetée ; limites invalides rejetées.

## Réserves
Le rendu basse résolution peut manquer des détails sous-pixel ; ce n'est pas une certification de fidélité absolue, ni un test interactif Windows. Les moteurs de rendu peuvent varier selon leurs versions. La comparaison stricte peut refuser certains PDF pourtant visuellement proches. Pas de fausses captures d'écran.
