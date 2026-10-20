# OpenPDF Studio V43.1 — Extraction et réorganisation fiables
Auteur : Abdelhalim Talbi

## Améliorations fonctionnelles
- Extraction : capture de l'identité de la source avant traitement, nouvelle vérification avant publication.
- Réorganisation : même protection contre les changements concurrents.
- En cas de changement, refus de publication et suppression du temporaire.
- Quatre tests sur PDF réels : extraction normale, réorganisation normale, modification concurrente pour chacune.
- Préservation des garanties précédentes : publication exclusive, validation du nombre de pages, empreinte SHA-256.

## Limites
La comparaison des métadonnées ne remplace pas le verrouillage du PDF source. Les tests CI Windows ne sont pas des captures d'une session utilisateur interactive.
