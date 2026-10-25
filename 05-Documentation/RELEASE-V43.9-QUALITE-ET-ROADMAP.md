# OpenPDF Studio V43.9 — Fraîcheur du cache d'aperçu
Auteur : Abdelhalim Talbi

## Correction
L'aperçu PDF pouvait conserver des pages en cache après modification du document source par une autre application. Le cache est maintenant indexé par chemin, numéro de page, taille du fichier et horodatage de modification haute résolution.

- Une modification de taille ou de date de modification invalide l'entrée antérieure.
- Les pages distinctes conservent des clés différentes.
- Le nombre maximal de douze aperçus en cache est conservé.
- Quatre tests de régression sur source stable, modifiée, page différente et source absente.

## Limites
Le cache repose sur des métadonnées et non sur une empreinte cryptographique. Une modification qui conserve taille et horodatage peut échapper à l'invalidation. Recette interactive Windows non encore réalisée.
