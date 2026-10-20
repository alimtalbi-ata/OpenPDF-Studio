# OpenPDF Studio V43.2 — Cohérence des sources lors du découpage transactionnel
Auteur : Abdelhalim Talbi

## Évolution
- Capture des métadonnées du PDF source avant le découpage en lots.
- Vérification de l'identité de la source après création des PDF dans le dossier temporaire et avant la publication des fichiers finaux.
- Refus de publier si le PDF source a été modifié ; nettoyage de la transaction temporaire.
- Deux tests sur un PDF réel de deux pages : découpage normal et modification simulée du source avant publication.

## Limites
La publication de plusieurs fichiers n'est pas une opération atomique unique. Le contrôle de métadonnées n'est pas un verrouillage cryptographique. Une modification après la vérification finale reste possible. Qualification Windows automatisée et recette GUI interactive restent distinctes.
