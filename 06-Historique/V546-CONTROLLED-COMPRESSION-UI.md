# Historique V546 — Compression contrôlée dans l’interface

- **25/10/2026** — Création de la branche dédiée V546 à partir de la tête V545 `724863da384b9e6e98fecfc9250f903dc7828bc3`.
- **Produit** — Exposition des profils Images adaptatif et Automatique contrôlé ; libellés explicites en français et conservation des identifiants moteur historiques.
- **Sécurité UX** — Consentement et aperçu obligatoires avant les profils avec perte.
- **Mesure** — Résumé avant/après en octets et pourcentage, preuves RGB/alpha/structure bornées, limites documentées.
- **Traitement** — Le profil automatique utilise le dispatcher réservé et le moteur qualité existant ; le no-gain est audité comme `no_output`.
- **Qualification** — Workflow Ubuntu/Windows dédié ajouté ; résultats finaux à confirmer à partir des runs associés au commit final de la PR. Aucun résultat non observé n’est anticipé.
- **Gouvernance** — `main` préservée, aucun merge automatique. Auteur : Abdelhalim Talbi.
- **25/10/2026 — V546.1** — Résultat de compression enrichi avec mesures comparatives par candidat (taille/gain, MAE, pixels modifiés, durée) et motifs de rejet typés ; aucun texte d’exception brut ni chemin absolu n’est réaffiché. Tests ciblés étendus.
