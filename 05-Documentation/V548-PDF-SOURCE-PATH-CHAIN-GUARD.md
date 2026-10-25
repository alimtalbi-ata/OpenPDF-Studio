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

## Qualification reproductible et provenance

Le workflow `.github/workflows/page-order-v497.yml` exécute les tests V548 et les régressions de pages sur Ubuntu et Windows. Le workflow `.github/workflows/source-closure-v502.yml` vérifie la fermeture des sources, les régressions Office/OCR, les exécutables Windows natifs et l'installation/désinstallation avant le packaging.

Le script `02-Compilation/write_v548_ci_qualification.py` relie les reçus au SHA exact du commit courant. Il refuse de réutiliser un ancien run vert du même PR, vérifie les sept résultats V548 par système, les empreintes SHA-256 des exécutables et les reçus natifs. Il n'écrit qu'un état agrégé sans texte des documents ni journaux bruts. Le ZIP cumulatif doit inclure `04-Tests-et-Qualification/V548-CI-QUALIFICATION.json`; la génération du guide signale « NON VÉRIFIÉE » si le reçu est absent, ancien, incomplet ou s'il contient un test ignoré.

Les statuts à citer sont ceux du run propre au SHA courant. La qualification statique, les tests fonctionnels Ubuntu/Windows, les smoke tests natifs Windows et la revue graphique humaine restent des catégories distinctes ; le passage des premières ne doit jamais être présenté comme une preuve de la dernière.

## Limites et compatibilité

- L'utilisation d'un chemin PDF traversant une jonction ou un lien symbolique est désormais refusée, même si la cible est valide. Les chemins physiques réguliers restent acceptés.
- La garde est un précontrôle par chemin et ne constitue pas une défense complète contre une course TOCTOU si un processus hostile remplace un composant après sa vérification. Une ouverture ancrée sur des descripteurs de répertoires et une copie source privée serait une évolution distincte.
- Les hard links ne sont pas distingués des fichiers ordinaires.
- Le contrôle ne vérifie ni le contenu malveillant, ni l'authenticité du PDF, ni la fidélité de conversion.
- Aucune revue graphique humaine Windows ni signature Authenticode n'est revendiquée.
- Le numéro applicatif reste **51.4** ; V548 est un jalon de développement, pas une nouvelle version publiée.

**Aucun merge automatique : `main` est préservée.**
