# OpenPDF Studio V43.8 — Navigation rapide et aperçu asynchrone
Auteur : Abdelhalim Talbi

## Incident évité
Deux demandes d'aperçu successives pour la même page peuvent appartenir à des générations différentes. Dans l'ancienne implémentation, une demande récente était supprimée si un rendu précédent était encore en cours. Le résultat de ce rendu précédent était ensuite rejeté, laissant l'interface bloquée sur « Chargement de l'aperçu ».

## Correction
- Les travaux d'aperçu en attente sont identifiés par la page ET la génération de navigation.
- Une nouvelle génération lance son propre rendu, même si la même page était demandée précédemment.
- Les résultats obsolètes restent rejetés par la vérification de génération.
- Deux tests de non-régression vérifient le lancement de la nouvelle demande et le rejet d'une demande ancienne.

## Limites
L'amélioration corrige la cohérence de la navigation, sans constituer une mesure de performance ni une recette manuelle de l'interface Windows.
