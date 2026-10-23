# OpenPDF Studio V51.0 — Prévalidation OCR des conversions Office éditables

**Auteur : Abdelhalim Talbi — 23 octobre 2026.**

## Objectif produit

Empêcher qu'un PDF composé d'images de pages numérisées soit silencieusement converti en DOCX/XLSX/PPTX vide ou incomplet. Le nouveau contrôle `openpdf_office_scan_gate_v510.py` classe chaque page en `extractable_text`, `scanned_image_only`, `graphics_without_extractable_text` ou `blank` sans enregistrer le texte du document.

Une page sans texte extractible et dont les images raster occupent au moins 65 % de la surface visible est classée comme numérisée. Le calcul utilise l'union exacte des rectangles d'images, ce qui évite de compter plusieurs fois des images superposées. Les pages numérisées bloquent la conversion Office avant la création du fichier temporaire ; l'utilisateur doit d'abord réaliser un OCR. Les pages réellement blanches restent acceptées. Une page contenant uniquement de petits graphiques génère un avertissement de fidélité.

## Parcours et sécurité

`PDF source -> SHA-256 -> analyse de toutes les pages -> [scan >= 65 % sans texte ?] -> rejet OCR requis OU conversion -> audit OOXML -> vérification exacte du texte -> SHA-256 -> publication exclusive`.

Contrôles : refus de PDF chiffré, lien symbolique source, nombre de pages > 5 000, plus de 512 rectangles raster par page, géométrie invalide, source modifiée pendant l'analyse, destination existante. Le rapport CLI est un JSON contenant des nombres et classifications, sans texte extrait. Code de retour 2 pour OCR requis, 0 pour passage.

## Validation vérifiable

- 12 nouveaux tests sur de vrais PDF synthétiques : pages numérisées, mixtes, texte sur image, page blanche, petit logo, PDF chiffré, symlink, destination préexistante, SHA-256, JSON et union de rectangles.
- Régressions Office V45.9, V46.0, V45.7 et V40.9 vérifiées localement sous Linux.
- Fermeture statique : 91 modules, aucun manquant.
- La qualification Windows native V51.0, les tests CI GitHub et la validation GUI humaine sont des étapes distinctes : ne pas les présenter comme réussies avant les journaux effectifs.

## Limites explicites

Le seuil 65 % est heuristique : un scan en petits fragments peut ne pas être détecté, une image de fond peut être classée comme scan, et la présence de texte extractible ne prouve pas la qualité OCR. Le moteur Office exporte du texte éditable, **pas** une reconstruction garantie des images, tableaux, polices ou de la géométrie du PDF. Aucune preuve de fidélité visuelle ou de qualification humaine Windows n'est revendiquée.

## Prochaines priorités

Parcours OCR -> conversion Office assisté, mesure de couverture texte et qualité OCR par page, puis qualification UI Windows avec captures authentiques et corpus métier autorisé.
