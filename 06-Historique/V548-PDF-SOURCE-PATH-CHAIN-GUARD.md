# Historique V548 — Garde de la chaîne de chemin source PDF

**Auteur : Abdelhalim Talbi — 26 octobre 2026**

- Étend V547 : détection des liens symboliques et jonctions Windows sur tous les composants du chemin lexical, pas seulement le fichier final.
- Applique la garde avant normalisation aux points d'entrée du dispatcher et au service de pages.
- Ajoute des tests d'ordre de contrôle, alias parent, `..`, chemin valide, chemin manquant et absence de publication.
- Met à jour le manifeste des modules runtime Windows et les pins SHA-256.
- Qualification CI du commit V548 : en attente de résultats GitHub Actions au moment de la préparation de cette révision.
- Limites non masquées : course TOCTOU après précontrôle, hard links, absence d'audit malware, absence de revue GUI Windows humaine et d'Authenticode.
