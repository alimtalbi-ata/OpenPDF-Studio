# OpenPDF Studio V538 — Fidélité sémantique de la compression

**Auteur : Abdelhalim Talbi**  
**Date : 25 octobre 2026**  
**Base : V537, PR #44, commit d69e5293bfa24985cb179300eb1e6464b80f10a5**

## Problème reproduit

Le vérificateur de compression indépendant V48.9 comparait la taille, le texte extrait, la géométrie et tous les pixels RGB à échelle bornée. Un PDF candidat plus petit pouvait néanmoins perdre des liens hypertexte, signets, annotations ou métadonnées, tout en conservant le même rendu et le même texte. Quatre cas de perte ont été acceptés **avant** le correctif. Ce sont des défauts de qualification de compression, pas des défauts démontrés du moteur principal, qui possédait déjà un garde-fou structurel.

## Correctif V538

Le vérificateur indépendant `openpdf_compression_acceptance_v489.py` appelle désormais le garde-fou de production `validate_structure_preserved()` **avant** de rendre les pages. Les différences de structure refusent le candidat. Les catégories comprennent : métadonnées descriptives, étiquettes de pages, signets, pièces jointes, liens, annotations, formulaires, calques, visibilité, langue et accessibilité/XMP. Les actions automatiques, signatures et PDF protégés sont refusés par le garde-fou existant. L'audit reste local et en lecture seule.

Le rapport d'acceptation comporte `structure` avec les compteurs `pages_verified`, `links_verified`, `annotations_verified`, `widgets_verified`, `attachments_verified`, `bookmarks_verified` et `layers_verified`. Le vérificateur des reçus `verified_evidence()` rejette un rapport sans preuve structurelle complète et propage ces compteurs vers la qualité de la compression automatique. La vérification des empreintes SHA-256 avant/après audit reste en place.

## Qualification réelle et limites

Sur PDF synthétiques réels (PyMuPDF), 7 nouveaux tests V538 couvrent 4 pertes invisibles, la conservation d'un lien et d'un signet, la compression automatique de bout en bout et le refus d'un reçu structurel incomplet. Avant correctif : **4 tests échoués et 2 erreurs** ; après correctif : **7/7 réussis**. Campagne locale ciblée Linux : **134/134 tests réussis**, 0 ignoré (13 modules). Les campagnes CI Ubuntu/Windows et la qualification native Windows sont à vérifier sur le commit publié : les résultats Linux ne les remplacent pas.

**Limites :** les pixels sont comparés à l'échelle définie par la politique ; cela ne certifie ni l'impression, ni l'OCR, ni le PDF/A. La comparaison structurelle repose sur les objets pris en charge par le garde-fou de production. Les PDF interactifs non vérifiables sont refusés plutôt qu'acceptés silencieusement. Le test n'établit pas l'absence de vulnérabilités du moteur PDF.

## Commandes de contrôle

```bash
python -m unittest discover -s 04-Tests-et-Qualification -p test_compression_semantics_v538.py -v
python -m unittest discover -s 04-Tests-et-Qualification -p test_compression_acceptance_v489.py -v
python -m unittest discover -s 04-Tests-et-Qualification -p test_auto_compression_v505.py -v
```

## Prochaine priorité

Mesurer les conversions OCR/Office sur des documents métier annotés indépendamment, avec précision/rappel par page et contrôle d'intégrité des références. Qualifier l'interface Windows de façon interactive et signer les exécutables.
