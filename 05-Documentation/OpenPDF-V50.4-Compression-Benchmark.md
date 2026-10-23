# OpenPDF Studio V50.4 — Benchmark de compression mesuré

**Auteur : Abdelhalim Talbi** — 23 octobre 2026.

## Objectif

La commande `openpdf_compression_benchmark_v504.py` exécute le moteur **réel** de compression de l'application sur un corpus de PDF et génère un reçu JSON contenant les tailles avant/après, les gains en octets et pourcentage, le temps écoulé, les empreintes SHA-256 et les métriques de fidélité RGB. Les contrôles sont exécutés **avant publication** des candidats grâce au service `CompressionRequest` et à `CompressionQualityGate` avec `sample_step=1`.

## Utilisation

```powershell
python 03-Sources/openpdf_compression_benchmark_v504.py document1.pdf document2.pdf --output-dir preuves-compression --profiles standard,smaller_only --min-saving-percent 1 --strict
```

Le répertoire de sortie doit être **absent**. Un répertoire existant ou un PDF d'entrée en lien symbolique est refusé. Les entrées sont plafonnées à 12 PDF, 50 Mio par PDF et 200 Mio au total. Le budget de rendu du contrôleur existant s'applique également.

`--min-saving-percent` est facultatif. Lorsqu'il est renseigné, le seuil de gain est contrôlé sur le candidat privé **avant publication** par `AcceptancePolicy`. Un candidat rejeté ne doit pas créer de PDF de sortie. Sans ce paramètre, le profil `standard` peut produire un PDF plus volumineux : le rapport indique alors un `saved_bytes` négatif, sans le qualifier de gain.

## États et limites

- `published` : PDF publié, taille, empreinte et qualité effectivement mesurées.
- `no_gain` : moteur sans publication ; aucune taille de sortie fictive.
- `rejected` : erreur ou seuil non satisfait ; aucune métrique de succès fabriquée.

La métrique MAE est une erreur moyenne par canal RGB (0 à 255), la fraction de pixels modifiés est mesurée à l'échelle choisie, sur toutes les pages retenues. **Ce n'est pas une certification PDF/A, de qualité d'impression, d'accessibilité, d'OCR ou de fidélité sémantique complète.** Le temps est mesuré par `perf_counter`, dépend de la machine et n'est pas comparable sans environnement contrôlé.

## Qualification

Les tests V50.4 utilisent un PDF réel avec texte et graphique vectoriel, des essais de réduction, un seuil de gain refusé avant publication, des fichiers corrompus, la non-substitution de destination et des budgets d'entrée. La CI dédiée lance les tests sur Ubuntu et Windows, mais ne constitue pas à elle seule une validation humaine de l'interface graphique.

## Résultats complémentaires sur image synthétique

Sur un PDF réel créé pour le test avec une image raster synthétique : **1 533 877 octets** à l’entrée ; profil `standard` : **1 454 692 octets (5,16 %)** ; `images_balanced` : **202 816 octets (86,78 %)** avec MAE **0,5338/255** ; `images_adaptive` : **136 938 octets (91,07 %)** avec MAE **0,7260/255**. Ces gains sont propres à ce document synthétique et ne prédisent pas ceux d’un corpus métier. Les reçus JSON et PDF réels sont inclus dans le ZIP.

## Architecture

`PDF corpus` → `Input budgets / SHA-256` → `CompressionRequest` → `Private candidate` → `RGB quality gate + optional saving gate` → `Exclusive publication` → `JSON evidence + elapsed time`.

## Prochaine étape

Corpus représentatif de documents clients **anonymisés**, mesures multi-profils et comparaison des temps/mémoires sur Windows natif, puis validation GUI manuelle.
