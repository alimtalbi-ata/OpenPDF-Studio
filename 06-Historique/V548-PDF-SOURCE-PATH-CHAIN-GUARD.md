# Historique V548 — Garde de la chaîne de chemin source PDF

**Auteur : Abdelhalim Talbi — 26 octobre 2026**

- Étend V547 : détection des liens symboliques et jonctions Windows sur tous les composants du chemin lexical, pas seulement le fichier final.
- Applique la garde avant normalisation aux points d'entrée du dispatcher et au service de pages.
- Ajoute des tests d'ordre de contrôle, alias parent, `..`, chemin valide, chemin manquant et absence de publication.
- Met à jour le manifeste des modules runtime Windows et les pins SHA-256.
- Ajout d'un réconciliateur CI lié au SHA exact : les reçus de tests et de binaires natifs sont agrégés sans copier les journaux bruts. Le pipeline échoue en cas de run absent/ancien, test ignoré, hash incohérent ou reçu Windows incomplet.
- Le guide Word/PDF ne réutilise plus les anciens nombres de tests/modules ; il vérifie le schéma et le SHA du reçu courant avant d'afficher une qualification PASS. Le run de packaging doit rester vert pour valider le ZIP cumulatif.
- Limites non masquées : course TOCTOU après précontrôle, hard links, absence d'audit malware, absence de revue GUI Windows humaine et d'Authenticode.
