# OpenPDF Studio V44.2 — Récupération sûre des transactions incomplètes
Auteur : Abdelhalim Talbi

## Correction
Avant suppression de sorties publiées, la récupération vérifie désormais la présence et le type de chaque fichier déclaré dans le staging. Si un fichier manque ou est un lien symbolique, la transaction reste intacte et le rapport indique « manual_review_missing_staged_output ».

Cette protection évite de traiter automatiquement une transaction dont les preuves de staging sont incomplètes, même si le journal est syntaxiquement valide.

## Tests
- Staging incomplet : aucune sortie publiée supprimée, dossier conservé.
- Staging complet avec liens physiques : récupération et nettoyage attendus.
- Deux tests de régression ajoutés à GitHub Actions Windows.

## Limites
Le mécanisme suppose l'usage du verrou coopératif de dossier; une intervention concurrente extérieure reste hors contrat. Recette GUI Windows manuelle distincte.
