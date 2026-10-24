# OpenPDF Studio V44.1 — Récupération transactionnelle stricte
Auteur : Abdelhalim Talbi

## Correction
La récupération des découpages interrompus vérifiait la version du journal et les noms de fichiers, mais ne vérifiait pas son état transactionnel. Un journal avec état inattendu pouvait déclencher la suppression de sorties liées au dossier de staging.

La récupération accepte désormais exclusivement un journal de schéma 1 à l'état « prepared ». Tout état inattendu produit « manual_review_invalid_journal » sans suppression automatique.

## Tests
- Journal d'état invalide : conservation du dossier de staging et du fichier de sortie.
- Journal préparé valide : récupération de la sortie liée et suppression du staging.
- Tests intégrés au workflow Windows.

## Limites
La récupération doit toujours être effectuée sous réservation coopérative via le contrôleur. Les fichiers étrangers ou journaux malformés nécessitent une revue manuelle. La qualification Windows CI ne remplace pas une recette GUI.
