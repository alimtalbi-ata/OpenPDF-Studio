# OpenPDF Studio V50.8 — Fidélité de la transparence PDF

**Auteur : Abdelhalim Talbi.** Date : 23 octobre 2026.

## Amélioration vérifiable

Le rendu RGB sur fond blanc ne révèle pas toutes les altérations de transparence. Le module `openpdf_compression_alpha_v508.py` compare tous les échantillons alpha RGBA à l'échelle bornée définie dans la politique de compression, sur toutes les pages et annotations. Le contrôle indépendant s'exécute sur les candidats temporaires, avant publication exclusive. Il vérifie les empreintes SHA-256 avant et après l'audit, les géométries et les budgets de pixels.

Le reçu inclut les pixels transparents, translucides et opaques, le nombre de pages et de pixels vérifiés, l'échelle, et les empreintes des fichiers. Tout changement alpha rejette le candidat. La compatibilité avec le schéma historique V50.6 est conservée.

## Qualification et limites

14 nouveaux tests fonctionnels locaux ont réussi, avec vrais PDF synthétiques (y compris deux rendus RGB sur blanc identiques mais des canaux alpha différents). Les régressions V50.5/V50.6/V50.7 ont été rejouées localement. Les résultats CI Linux/Windows et les constructions natives Windows sont vérifiés séparément dans GitHub Actions ; aucune qualification graphique humaine n'est inférée.

La comparaison porte sur les pixels à l'échelle de rendu configurée (0,5 par défaut). Elle n'est pas une certification de conformité PDF/A, impression, OCR, accessibilité ou fidélité à haute résolution.

## Priorités suivantes

Élargir le corpus métier (scans, tableaux, calques, formulaires, transparences complexes), mesurer le coût CPU/mémoire, qualifier l'interface Windows par captures réelles et renforcer les conversions Office éditables.
