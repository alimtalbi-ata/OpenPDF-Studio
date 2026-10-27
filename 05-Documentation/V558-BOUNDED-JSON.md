# OpenPDF Studio V51.4 / V558 — Bornes strictes du JSON de publication

Auteur : Abdelhalim Talbi  
Branche dédiée : feature/v51.4-bounded-json-release-parsing-v558-20261027  
Base empilée : V557, PR #63.

La branche main reste intacte ; aucune fusion automatique.

## Risque traité

Le parseur V557 refusait les clés dupliquées et les valeurs numériques non finies. Il restait exposé aux JSON excessivement volumineux ou profondément imbriqués, aux entiers hors de toute plage utile pour des reçus de livraison, et aux chaînes JSON comportant des substituts Unicode UTF-16 isolés, dont les consommateurs peuvent diverger dans leur traitement.

## Renforcement V558

- Plafond de 32 MiB pour toute charge JSON de preuve, avant l'analyse.
- Plafond de 128 niveaux d'objets/tableaux, comptés hors des chaînes et avant le parseur récursif.
- Entiers limités à la plage signée 64 bits, avec vérification de la longueur du jeton avant conversion.
- Refus des substituts Unicode isolés dans les clés et les valeurs ; les caractères supplémentaires Unicode valides restent acceptés.
- Conservation de tous les contrôles V557 : clés uniques, nombres finis, UTF-8 contrôlé et BOM UTF-8 accepté.

## Tests et CI

La suite fonctionnelle couvre les seuils avant appel au parseur, les niveaux de nesting à la limite, les entiers minimum/maximum et hors plage, les substituts Unicode isolés, le caractère supplémentaire valide, les duplications JSON et la vérification d'un inventaire ZIP cohérent ou ambigu. Les tests sont reliés au workflow source-closure-v502.yml sur Ubuntu et Windows, puis le workflow reconstruit les binaires Windows natifs et l'archive cumulative.

Les contrôles unitaires/fonctionnels, la fermeture des sources, la construction du portable, le build/installateur natif, l'installation/lancement/désinstallation et la validation finale du ZIP sont des étapes distinctes. Aucun résultat de livraison V558 n'est présumé avant les exécutions liées au SHA exact.

## Limites

Ces bornes ne démontrent pas l'absence de toute vulnérabilité dans tous les parseurs JSON. SHA-256 vérifie l'intégrité des octets comparés, pas l'identité de l'éditeur. Aucun secret de signature n'est stocké dans le dépôt ; aucune signature Authenticode, revue graphique humaine Windows ou fidélité OCR/Office certifiée n'est revendiquée.

## Prochaine priorité

Après qualification exacte-SHA, mesurer la fidélité PDF vers DOCX/XLSX/PPTX sur un corpus métier annoté indépendamment : précision, rappel, ordre des objets, géométrie et fidélité visuelle.
