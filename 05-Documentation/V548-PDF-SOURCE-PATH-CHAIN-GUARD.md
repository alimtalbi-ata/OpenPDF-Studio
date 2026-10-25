# OpenPDF Studio V548 — Garde de toute la chaîne de chemin source PDF

**Auteur : Abdelhalim Talbi**  
**Date : 26 octobre 2026**  
**Branche :** `feature/v51.4-source-path-chain-guard-v548-20261026`  
**Base :** V547 / PR #54

## Problème corrigé

V547 rejetait un lien symbolique placé directement sur le fichier PDF, mais autorisait encore un alias dont un répertoire parent était un lien symbolique. La résolution du chemin pouvait alors masquer ce composant. Sous Windows, une jonction de répertoire constitue également un alias à contrôler.

## Changement produit

- Nouveau module commun `openpdf_source_path_guard_v548.py`.
- Parcours du chemin lexical absolu composant par composant, avant toute canonicalisation.
- Refus des liens symboliques et des jonctions Windows sur le chemin source, y compris lorsque le chemin contient ensuite `..`.
- Validation qu'il s'agit d'un fichier PDF régulier existant.
- Intégration dans le dispatcher pour compression, fusion, extraction, découpage, réorganisation et conversions Word/Excel/PowerPoint, ainsi que dans le service de pages atomiques.
- Nouveau test fonctionnel ciblé sur les alias parents, l'ordre des contrôles, l'absence de sortie, les opérations PDF et le parcours Office.
- Mise à jour du manifeste d'exécution Windows et des SHA-256 des modules source modifiés.

Les noms de chemins ne sont pas inclus dans les messages de refus. Le comportement de traitement PDF reste inchangé pour les chemins réguliers sans alias.

## Qualification à effectuer

Le workflow `.github/workflows/page-order-v497.yml` est configuré pour exécuter le test V548 sur Ubuntu et Windows, en plus des régressions V547 et de réorganisation de pages. Le workflow de fermeture des sources doit vérifier que le nouveau module est inclus dans la fermeture statique et dans le manifeste runtime, puis reconstruire les artefacts Windows natifs et le ZIP cumulatif.

Les résultats ne seront revendiqués qu'après l'exécution des workflows du commit de cette PR. Les contrôles statiques, tests fonctionnels et qualifications natives Windows restent des catégories distinctes.

## Limites et compatibilité

- L'utilisation d'un chemin PDF traversant une jonction ou un lien symbolique est désormais refusée, même si la cible est valide. Les chemins physiques réguliers restent acceptés.
- La garde est un précontrôle par chemin et ne constitue pas une défense complète contre une course TOCTOU si un processus hostile remplace un composant après sa vérification. Une ouverture ancrée sur des descripteurs de répertoires et une copie source privée serait une évolution distincte.
- Les hard links ne sont pas distingués des fichiers ordinaires.
- Le contrôle ne vérifie ni le contenu malveillant, ni l'authenticité du PDF, ni la fidélité de conversion.
- Aucune revue graphique humaine Windows ni signature Authenticode n'est revendiquée.
- Le numéro applicatif reste **51.4** ; V548 est un jalon de développement, pas une nouvelle version publiée.

**Aucun merge automatique : `main` est préservée.**
