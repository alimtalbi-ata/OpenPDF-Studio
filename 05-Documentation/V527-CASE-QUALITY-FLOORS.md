# OpenPDF Studio V51.4 / V527 — seuils de fidélité par document

**Auteur : Abdelhalim Talbi** · **Statut : changement de qualification, non inclus dans les exécutables V51.4**.

## Contexte et défaut corrigé

Le gate V519 utilisait des ratios micro-moyennés sur tous les documents du corpus. Une conversion catastrophique sur un petit PDF pouvait être masquée par un grand document correct : par exemple 1 cellule correcte sur 2, plus 100 sur 100, donne 101/102 = 99,02 % et dépasse un seuil global de 90 %. Le résultat PASS ne garantissait donc pas une qualité minimale pour chaque document.

## Solution V527

Trois paramètres **optionnels** dans `thresholds` du manifeste V519 :

- `min_case_nonempty_cell_accuracy` : précision minimale de cellules non vides pour **chaque** PDF, entre 0 et 1.
- `min_case_table_recall` : rappel minimal des tableaux pour **chaque** PDF, entre 0 et 1.
- `max_case_extra_nonempty_cells` : nombre maximal de cellules non vides inventées dans **chaque** XLSX.

L'ancien schéma reste valide : aucun de ces paramètres n'est requis. Lorsqu'un seuil individuel est activé, le contrôle refuse les cas sans dénominateur mesurable, compare les fractions **avant arrondi** et retourne FAIL si au moins un document viole un plancher. Le rapport inclut uniquement les pires ratios et le nombre de cas en échec, jamais les noms de fichiers ou le texte métier.

Exemple à ajouter à un manifeste existant :

```json
{
  "min_case_nonempty_cell_accuracy": 0.90,
  "min_case_table_recall": 0.90,
  "max_case_extra_nonempty_cells": 0
}
```

Ces clés s'ajoutent aux cinq seuils V519 obligatoires, elles ne les remplacent pas.

## Architecture

```
Manifest JSON + fichiers PDF/XLSX + annotations indépendantes
      |
      v
V517 : vérification SHA-256, sécurité OOXML, comparaison cellule/table
      |
      v
V519/V527 : agrégation micro-moyennée + planchers individuels optionnels
      |                              |
      +--> FAIL si seuil global      +--> FAIL si un cas est sous le seuil
      |
      v
Rapport sans contenu métier (PASS / FAIL, métriques, empreintes)
```

## Qualification

- 7 nouveaux tests V527, dont deux conversions PDF synthétiques réelles vers XLSX, modification volontaire d'une cellule et démonstration PASS global incorrect / FAIL individuel correct.
- Suite Excel locale Linux : 119 tests réussis, aucune erreur (environnement Python 3.13, PyMuPDF 1.26.7, openpyxl 3.1.5).
- CI Ubuntu/Windows : résultats à consulter sur la PR, ne pas considérer le build Windows comme qualifié avant publication de ses jobs.
- Documents métier humains, fidélité visuelle, GUI Windows humaine et signature Authenticode : **non évalués**.

## Risques / prochaines actions

Les annotations `human_reviewed` sont déclaratives, sans chaîne de validation humaine signée. Construire un corpus métier réellement annoté et auditable, puis intégrer des planchers individuels dans les critères de release. Préserver `main` et ne pas fusionner automatiquement.
