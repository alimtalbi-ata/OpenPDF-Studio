# V521 — Détection des tableaux et fusions fantômes dans les conversions PDF → XLSX

**Auteur : Abdelhalim Talbi — 24 octobre 2026.**

## Anomalie confirmée avant correction
Le gate `openpdf_xlsx_corpus_gate_v519.py` vérifiait le rappel des tableaux/fusions, l'exactitude des cellules non vides et les valeurs supplémentaires. Il n'imposait aucune contrainte de précision structurelle. Un XLSX avec une feuille de tableau vide supplémentaire et/ou une plage fusionnée vide supplémentaire pouvait obtenir **PASS**, malgré `table_precision < 1` ou `merge_precision < 1`. Reproduction locale : deux PDF synthétiques convertis en XLSX réels, deux structures ajoutées ; **PASS erroné** avant correction.

## Correction
Le gate refuse désormais toute structure non justifiée par la vérité terrain : `observed_tables != matched_tables` entraîne `unexpected_tables`, et `observed_merges != matched_merges` entraîne `unexpected_merges`. Les seuils et le schéma `openpdf.xlsx.corpus.v1` restent compatibles. Une sortie est **FAIL** si une de ces conditions est rencontrée, même si toutes les cellules non vides sont correctes et qu'aucune valeur n'est inventée.

## Tests et limites
`test_xlsx_phantom_structures_v521.py` exécute deux vraies conversions PDF → XLSX, vérifie le cas sain et les cas malveillants, puis contrôle l'absence de fuite de texte métier dans le rapport. Les annotations sont **synthétiques connues à la génération**, jamais présentées comme validation humaine. Ce contrôle est un outil de qualification Python ; il n'ajoute pas de fonctionnalité à l'interface Windows et ne mesure pas la fidélité visuelle. Les exécutables V51.4 antérieurs ne sont pas reconstruits par cette modification.

## Exécution
`python -m unittest discover -s 04-Tests-et-Qualification -p test_xlsx_phantom_structures_v521.py -v`

## Prochaine priorité
Corpus métier réellement annoté, avec vérification indépendante des tableaux sans bordures, scans, cellules fusionnées et documents multipages ; validation de la fidélité et des performances sur Windows réel.
