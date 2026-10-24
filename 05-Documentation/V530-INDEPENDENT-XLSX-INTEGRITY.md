# OpenPDF Studio — V530 : intégrité de la vérité terrain Excel

**Auteur : Abdelhalim Talbi**  
**Statut : correction de l'outil Python de qualification, non embarquée dans les exécutables Windows.**

## Défaut démontré

L'audit indépendant `openpdf_xlsx_ground_truth_v517.evaluate_ground_truth` pouvait retourner `PASS` pour un XLSX contenant une valeur inattendue en `E1`, `A2` ou `E2` sur une feuille de tableau, et accepter une feuille masquée. L'annotation JSON pouvait être modifiée entre son chargement et la publication du rapport sans vérification finale de son empreinte.

Les sept tests V530 ont reproduit **six échecs avant correction** (le contrôle hors grille `G4` passait déjà).

## Correction

- Toutes les feuilles doivent être visibles, y compris la feuille historique.
- Toute cellule non vide hors de la grille annotée, hormis la provenance `A1:D1`, augmente `extra_nonempty_cells` et entraîne `DEVIATION`.
- Le SHA-256 de l'annotation est revérifié après l'analyse, comme celui du PDF et du XLSX ; une mutation entraîne une erreur.
- Les données métier ne sont pas copiées dans les rapports.

## Vérification

```sh
python -m unittest discover -s 04-Tests-et-Qualification -p test_xlsx_ground_truth_integrity_v530.py -v
python -m unittest discover -s 04-Tests-et-Qualification -p 'test_xlsx_*.py' -q
```

**Preuve locale Linux** : 7/7 tests V530 et 139/139 tests Excel réussis. Les PDF sont **synthétiques**, les XLSX ont été effectivement convertis puis altérés pour vérifier les contrôles. Les résultats CI GitHub Windows doivent être vérifiés indépendamment avant de déclarer une qualification Windows.

## Risques et suite

La vérification ne garantit pas la fidélité visuelle ni l'exactitude d'annotations humaines ; aucune capture UI humaine n'est revendiquée. Prochaine priorité : un corpus métier indépendant, autorisé et annoté, puis amélioration du moteur sur les écarts constatés.
