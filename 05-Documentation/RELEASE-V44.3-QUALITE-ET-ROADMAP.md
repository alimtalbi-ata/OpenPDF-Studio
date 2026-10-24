# OpenPDF Studio V44.3 — Durcissement des journaux de récupération
Auteur : Abdelhalim Talbi

## Correction
La récupération refuse désormais les journaux transactionnels représentés par un lien symbolique et les manifestes sans aucun fichier déclaré. Un lien symbolique pouvait rediriger la lecture du journal hors du dossier de préparation; un manifeste vide permettait de nettoyer un dossier de staging sans preuve de fichiers attendus.

Les états rejetés entraînent « manual_review_invalid_journal », sans suppression de sorties ni du staging.

## Tests
- Manifeste vide : rejet et conservation du staging.
- Journal symbolique : rejet et conservation du fichier publié, lorsque le système autorise la création de liens symboliques.
- Intégration dans GitHub Actions Windows.

## Limites
La création de liens symboliques peut être interdite sur certains agents Windows; le test correspondant est alors explicitement ignoré. Les accès concurrents non coopératifs nécessitent une protection supplémentaire.
