# OpenPDF Studio V51.4 — V553 : identité des chemins dans les archives cumulatives

**Auteur : Abdelhalim Talbi**  
**Branche :** `feature/v51.4-archive-nfkc-collision-guard-v553-20261026`  
**Base :** publication Windows V551 (#58). `main` est préservée ; aucune fusion automatique.

## Problème traité

Le contrôle d'intégrité du paquet cumulatif détectait les doublons avec `casefold()` mais sans normalisation Unicode. Deux membres distincts dans le ZIP pouvaient donc devenir le même nom sur un extracteur qui applique NFKC, notamment sur Windows ou dans des chaînes de traitement inter-plateformes. Le contrôle des fichiers utilisés comme répertoires parents ne couvrait pas non plus toutes les entrées de répertoire explicites.

## Modification

- Ajout d'une identité de chemin d'archive basée sur NFKC + casefold, sans renommer les fichiers archivés.
- Refus des caractères de compatibilité qui modifient la structure des séparateurs après normalisation.
- Application du même contrôle à la liste SHA-256, au payload source, aux membres fichiers et répertoires de ZIP externes et aux collisions file/directory.
- Normalisation avant application des exclusions de sécurité (fichiers sensibles, extensions et répertoires exclus).
- Tests adversariaux déterministes pour les alias de membres, les doublons de répertoires, les séparateurs de compatibilité et les fichiers utilisés comme parents.

## Qualification

Le nouveau workflow exécute les tests V553 sur les runners Ubuntu et Windows. Les fixtures ZIP de cette suite sont des tests synthétiques conçus pour être rejetés ; elles ne constituent pas des preuves de build Windows ou des artefacts de publication. La qualification native et la reconstruction cumulative restent dépendantes de CI.

## Limites

NFKC + casefold est une politique conservatrice de collision pour la livraison multiplate-forme, pas une garantie universelle sur le comportement de tous les extracteurs. Le contrôle d'intégrité SHA-256 n'authentifie pas à lui seul l'auteur de l'archive ; aucune signature Authenticode n'est revendiquée. La fidélité OCR/Office et la revue graphique humaine Windows ne sont pas couvertes par ce changement.

## Prochaine priorité

Rejouer la qualification Windows et produire le ZIP cumulatif à partir du commit exact de PR, puis poursuivre la réduction des courses de publication par handles et la qualification métier des conversions éditables.
