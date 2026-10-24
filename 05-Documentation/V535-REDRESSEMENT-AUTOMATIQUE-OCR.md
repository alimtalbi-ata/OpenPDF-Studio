# OpenPDF Studio V535 — Redressement automatique prudent avant OCR

**Auteur : Abdelhalim Talbi**  
**Version applicative : 51.4 ; cycle de développement : V535**  
**Date : 25 octobre 2026**

## Objectif produit

Le redressement manuel V534 imposait de connaître l'angle d'inclinaison. V535 propose un mode **automatique explicitement activé** pour les pages raster numérisées, avant la conversion PDF vers Word, Excel ou PowerPoint. Le comportement historique reste inchangé par défaut.

## Architecture et déroulement

1. La GUI, le répartiteur ou la CLI active `auto_deskew=True` / `--auto-deskew` (valeur par défaut : désactivée).
2. Le service OCR conserve le précontrôle du document, la politique de sélection des pages, les limites de pixels et la validation des modèles OCR hors ligne.
3. Chaque page raster sélectionnée est réduite à un échantillon maximal de 900 × 900 pixels ; un masque de pixels sombres sert à mesurer la concentration des lignes de texte après rotation.
4. Les angles entiers entre −12° et +12° sont explorés ; un affinage de 0,25° est appliqué autour du meilleur candidat. Un gain significatif, un maximum local net et au moins trois bandes de texte sont exigés.
5. Si l'alignement est ambigu, **aucune rotation** n'est appliquée. Le résultat indique l'angle effectivement appliqué et le motif de décision, page par page.
6. L'OCR Tesseract local, la conversion Office et le contrôle SHA-256 existants se poursuivent ; le fichier n'est publié qu'après les validations de cohérence.

## Interfaces

- GUI Windows : cocher **OCR avant conversion**, puis **Redressement automatique**. Le champ d'angle manuel doit rester à zéro.
- CLI : `python 03-Sources/openpdf_ocr_office_pipeline_v511.py scan.pdf resultat.xlsx --language eng --editable-tables --auto-deskew`
- API Python : `convert_scanned_office(source, destination, language='eng', table_mode=True, auto_deskew=True)`.
- Métadonnées : `auto_deskew`, `deskew_pages` (numéro de page, angle et motif). Aucun score d'exactitude OCR n'est annoncé.

## Mesures et preuves

Sur un **PDF synthétique** incliné de +8°, le détecteur estime une contre-rotation de −8°. Le test d'intégration a extrait 12 cellules sur 12 dans un classeur XLSX éditable. La page horizontale, la page blanche et les petits rasters ne sont pas redressés. Les pages de texte natif sont préservées. Les options manuel et automatique sont incompatibles et rejetées avant toute publication.

**Limites** : tests sur synthèses, pas sur corpus métier indépendant ; les photographies, les déformations de perspective, les scans très bruités, les angles hors ±12° et le rognage des marges ne sont pas corrigés de façon garantie. La concentration des lignes ne mesure ni la précision des caractères OCR ni la fidélité visuelle Office.

## Qualification et sécurité

Les tests V535 couvrent les choix d'angle, les rejets, le routage GUI/API, les pages mixtes, le SHA-256 et une conversion OCR réelle. Les campagnes CI Ubuntu/Windows sont nécessaires pour la qualification multiplateforme. Une compilation et des tests automatisés Windows ne remplacent pas une qualification humaine interactive de la GUI.

Les binaires V534 ne doivent pas être présentés comme des binaires V535 tant qu'ils n'ont pas été reconstruits sur un runner Windows depuis le commit V535.

## Priorité suivante

V536 : corpus métier annoté indépendamment (précision/rappel OCR, tableaux et cellules), traitement des pages déformées, métriques de non-régression, puis qualification interactive Windows.
