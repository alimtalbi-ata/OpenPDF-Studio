# OpenPDF Studio V534 — Redressement manuel des pages numérisées

**Auteur : Abdelhalim Talbi — 24 octobre 2026.**

## Contexte et priorité
Les tableaux numérisés inclinés peuvent être invisibles pour l'extracteur géométrique PDF → Excel. La V533 savait contrôler la couverture et le nombre de cellules, mais ne corrigeait pas la géométrie des pixels avant l'OCR.

## Implémentation
- Nouveau paramètre opt-in `deskew_angle_degrees` (-12 à +12, 0 par défaut), propagé GUI → dispatcher → OCR Office → moteur Tesseract/PyMuPDF.
- La correction s'applique **uniquement aux pages raster sans texte natif**. Elle effectue une rotation des pixels avec Pillow, conserve le format de la page, le DPI, et remplit le fond en blanc. Le document source est immuable.
- CLI : `python 03-Sources/openpdf_ocr_office_pipeline_v511.py input.pdf output.xlsx --language eng --editable-tables --deskew-angle -8`.
- Pour un scan tourné de +8 degrés, utiliser -8 degrés ; il s'agit d'un angle fourni par l'opérateur, **pas d'une détection automatique**.
- Valeurs hors limites, NaN, infini, types non numériques et tentative de rotation de pages avec texte natif sont rejetés avant publication.
- En mode désactivé (0), le chemin de conversion historique reste inchangé.

## Preuve fonctionnelle synthétique
Fixture créée par rasterisation d'un tableau de 4 lignes × 3 colonnes, puis rotation de +8 degrés :
- Sans correction : aucun tableau détecté, aucun XLSX publié.
- Avec correction -8 degrés : 1 feuille de tableau éditable, 12 cellules non vides et 12 valeurs attendues vérifiées.
- SHA-256 du PDF source inchangé, empreinte du XLSX produite et contrôlée.
Cette fixture ne représente pas un document métier annoté indépendamment et ne certifie ni la précision OCR générale ni la fidélité visuelle.

## Qualification et limites
Les tests V534 sont dans `04-Tests-et-Qualification/test_ocr_deskew_v534.py`.
La CI installe sur Windows des modèles OCR eng/fra officiels épinglés par SHA-256 avant les tests pour éviter les anciens `skip` dus à l'absence de modèle.
Le redressement peut rogner les coins de la page (rotation sur un canevas de même taille) et ajouter du flou. Ne pas activer sur une page non inclinée. Il ne corrige pas la perspective, les pages gondolées, les cellules fusionnées ou les erreurs de reconnaissance.
La validation graphique humaine sous Windows et la signature Authenticode restent distinctes des tests CI.

## Chaîne
`PDF original → preflight et SHA-256 → pages scannées → correction raster opt-in → OCR local → PDF intermédiaire → tableaux → XLSX audité → publication exclusive`

## Prochaine priorité
Détection automatique prudente de l'angle et qualification sur documents métier annotés indépendamment ; compléter les tests réels de l'interface Windows.
