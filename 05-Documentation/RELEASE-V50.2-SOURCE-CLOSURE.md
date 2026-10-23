# OpenPDF Studio V50.2 — Gate de fermeture des dépendances

Auteur : **Abdelhalim Talbi** · 23 octobre 2026.

## Problème confirmé

Le candidat cumulatif local V50.1 possède 86 modules Python dans la fermeture statique des entrées application + outils de build. La branche GitHub héritée de V50.1 ne contient pas **43 de ces modules**. Le dépôt distant déclare toujours `VERSION.txt = 40.2`, contre `50.2` dans le nouveau candidat cumulatif. Une CI qui ne teste que les fonctions de pages ne prouve donc pas que le portable ou l'installateur Windows peut être produit.

## Modification V50.2

`03-Sources/openpdf_source_closure_v502.py` parcourt les imports locaux depuis les points d'entrée, sans exécuter le code inspecté. Il détecte les dépendances absentes, les erreurs de syntaxe, les imports dynamiques littéraux et les modules symlinkés. Le résultat JSON est déterministe et retourne un code d'échec en cas de dépendance manquante.

`02-Compilation/BUILD-WINDOWS-INSTALLER.cmd` lance le gate **avant** les installations pip et PyInstaller, conserve le rapport même en cas d'échec, corrige les chemins Python contenant des espaces et embarque `VERSION.txt` dans les exécutables. Le script GitHub reste calé sur la version distante 40.2 tant que la réconciliation n'est pas achevée.

## Vérification et limites

- 18 tests de non-régression V50.2 réalisés sous Linux local, tous réussis.
- Le candidat cumulatif local : 86 modules inspectés, 0 manquant.
- La branche distante avant V50.2 : 43 modules locaux nécessaires absents (inventaire des noms GitHub comparé au graphe du candidat).
- La CI V50.2 comporte des tests statiques Linux/Windows et **un job de fermeture bloquant**. Il est attendu que le job de fermeture échoue sur la branche distante incomplète : cet échec est volontairement visible.
- Aucune qualification native de binaire, d'installation/désinstallation Windows ou d'interface graphique n'est revendiquée.

## Suite prioritaire

Réconcilier les 43 modules nécessaires et leurs versions d'API avec les sources cumulatives, mettre à jour `VERSION.txt` uniquement lorsque le dépôt est cohérent, puis exécuter le build Windows et les tests d'installation natifs. Ne pas fusionner automatiquement cette PR.
