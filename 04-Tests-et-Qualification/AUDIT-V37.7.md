# Audit technique V37.7 — vérifications réelles sous Linux

## Anomalies constatées dans V37.6
- BUILD-WINDOWS-INSTALLER.cmd : journal V37.5, vérificateur V37.3, configuration Inno V37.6 introuvable.
- COMPILER-PORTABLE.cmd : appel d’un script dans le mauvais répertoire (03-Sources).
- Interface : titre et bandeau encore en V37.0.
- Services : openpdf_operations délègue encore au contrôleur historique v348.
- Sources : nombreux modules versionnés ; aucune suppression de modules sans preuve d’inutilisation.

## Corrections V37.7
- Un seul orchestrateur .cmd pour installer + portable ; wrappers corrigés.
- Vérificateur précompilation indépendant de Windows ; tests unitaires.
- Configuration Inno Setup V37.7 créée.
- Interface : version, sélection initiale, libellés et statut.

## Limites
- Aucune compilation Windows ni capture UI Windows dans cet environnement Linux.
- Les scripts .cmd et Inno Setup sont vérifiés statiquement ; leur exécution Windows doit être validée.
- L’architecture historique et la qualité des conversions exigent encore une refonte plus profonde.
