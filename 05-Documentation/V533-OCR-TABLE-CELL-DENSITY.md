# OpenPDF Studio V533 — Seuil de cellules OCR éditables par page

**Auteur : Abdelhalim Talbi**  
**Date : 24 octobre 2026**  
**Base : V532 / PR #39 — branche dédiée, sans fusion automatique**

## Problème produit

V532 permettait de vérifier qu'au moins un tableau avait été détecté sur chaque page numérisée. Une grille avec très peu de valeurs reconnues pouvait cependant satisfaire ce contrôle, alors qu'un classeur Excel peu exploitable était produit.

## Modification V533

- Extraction OCR locale et conversion PDF vers XLSX éditable inchangées par défaut.
- Comptage indépendant, page par page, des cellules extraites et des cellules réellement non vides dans les tableaux.
- Reçu JSON enrichi avec `table_cells_by_page` : `page`, `cells`, `nonempty_cells`.
- Nouveau seuil facultatif `--min-nonempty-table-cells-per-scanned-page N` (0–10000, 0 = désactivé).
- En cas de valeur insuffisante sur une page numérisée, conversion refusée avant publication ; le PDF source reste inchangé.
- Paramètre exposé dans l'interface Windows uniquement pour **Excel + OCR avant conversion + Tableaux éditables**, et propagé par le répartiteur métier.
- Validation stricte des types : booléens, nombres négatifs, chaînes et valeurs hors limites refusés.

## Exemples

```shell
python 03-Sources/openpdf_ocr_office_pipeline_v511.py scan.pdf tables.xlsx --language eng --editable-tables --min-nonempty-table-cells-per-scanned-page 12
```

Le résultat contient par exemple :

```json
"table_cells_by_page": [{"page": 1, "cells": 12, "nonempty_cells": 12}]
```

## Vérifications et limites

Qualification locale Linux : 8/8 tests V533, 152/152 tests OCR, 139/139 tests Excel, 12/12 tests de réconciliation des sources. Les scénarios OCR utilisent de vrais PDF synthétiques rasterisés et Tesseract anglais installé localement. Aucune précision OCR métier ni fidélité visuelle n'est certifiée. Le seuil compte les valeurs extraites, pas leur exactitude sémantique. Une page contenant beaucoup de mauvaises valeurs peut donc passer. L'interface Windows n'a pas été validée par un opérateur humain.

**Risques résiduels :** scans inclinés, cellules fusionnées, tableaux multipages, faux positifs de détection et modèles OCR absents de certains runners Windows.

**Prochaine priorité :** évaluation indépendante sur corpus métier annoté, mesure de précision/rappel et traitement des tableaux inclinés. Ne pas fusionner automatiquement dans `main`.
