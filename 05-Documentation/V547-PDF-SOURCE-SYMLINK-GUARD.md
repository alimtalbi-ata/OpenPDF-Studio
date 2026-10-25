# OpenPDF Studio V547 — Garde des sources PDF avant canonicalisation

**Auteur : Abdelhalim Talbi**  
**Date : 25 octobre 2026**  
**Branche :** `feature/v51.4-page-source-symlink-guard-v547-20261025`  
**Base :** V546 / PR #53, commit `7d89c2296c93469649942d686935bdd3d622511f`

## Risque corrigé

Le dispatcher et le service de pages normalisaient certains chemins via `Path.resolve()` avant d'avoir testé le composant final du chemin d'origine. Comme la résolution suit un lien symbolique, le chemin canonique ne permet plus de distinguer le chemin demandé par l'appelant du fichier cible. Le cas de découpage était particulièrement important : le dispatcher transmettait ensuite le chemin déjà résolu à la transaction de découpage.

## Modification

- Le service de pages vérifie que le chemin PDF fourni n'est pas un lien symbolique avant résolution stricte, puis recontrôle le chemin lexical après résolution.
- Le dispatcher rejette les alias finaux symboliques avant toute normalisation pour compression, fusion, extraction, découpage et réorganisation.
- Le parcours OCR vers Office conserve son refus existant des chemins source symboliques.
- Les transactions, empreintes source, sorties exclusives et contrôles de fidélité existants restent utilisés. Aucune sortie n'est publiée lorsqu'une source directe symbolique est détectée.
- Les tests de régression emploient un garde de chemin mocké pour vérifier le comportement sur Ubuntu et Windows, plus une intégration avec un vrai lien lorsque le système autorise sa création.

## Qualification attendue

Le workflow `.github/workflows/page-order-v497.yml` compile les modules modifiés et exécute les tests V547 avec les régressions réelles de réorganisation et d'exclusion. Le workflow `.github/workflows/source-closure-v502.yml` inclut aussi une étape `windows-cumulative-package` qui réassemble le portable et l'installateur depuis leurs artefacts de qualification Windows natifs, régénère le manifeste binaire combiné et le guide Word/PDF, produit le ZIP cumulatif puis vérifie l'inventaire, les CRC, les reçus et le SHA-256 avant d'exposer l'artefact CI. Les statuts doivent être lus dans GitHub Actions après chaque commit ; ce document ne transforme pas un test planifié en test réussi.

## Limites

La garde vise le dernier composant source du chemin ; les liens symboliques dans les répertoires parents sont autorisés. La vérification répétée réduit le risque de changement pendant la résolution, mais ne remplace pas une ouverture basée sur des descripteurs et des garanties anti-TOCTOU sur tous les systèmes de fichiers. Elle ne prouve ni authenticité du PDF ni absence de contenu malveillant.

Le numéro applicatif reste **51.4**. V547 identifie cette étape de développement, pas une nouvelle version applicative publiée. Aucun binaire Windows n'est revendiqué comme reconstruit par ce changement et aucune qualification GUI Windows interactive n'est revendiquée.
