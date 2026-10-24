# OpenPDF Studio V531 — OCR de tableaux numérisés vers Excel éditable

**Auteur : Abdelhalim Talbi — 24 octobre 2026.** Moteur V531, version applicative 51.4 inchangée.

## Besoin et correction

Avant V531, les options « OCR avant conversion » et « Tableaux Excel éditables » étaient incompatibles dans l'interface Windows. La chaîne OCR produisait une feuille de texte, sans les feuilles de tableaux du moteur XLSX.

V531 permet leur sélection simultanée et explicite pour le format XLSX :

`PDF image/mixte -> OCR local Tesseract -> PDF OCR temporaire -> extraction heuristique des tableaux -> XLSX éditable -> vérification des cellules et de la structure OOXML -> publication exclusive`.

La source PDF n'est jamais modifiée. En cas d'OCR insuffisant, d'absence de tableau détecté, d'erreur de conversion ou de contrôle d'intégrité, aucune sortie n'est publiée. Les options restent désactivées par défaut et DOCX/PPTX n'acceptent pas le mode tableaux.

## CLI

```shell
python 03-Sources/openpdf_ocr_office_pipeline_v511.py scan.pdf sortie.xlsx --language eng --editable-tables
```

Le modèle anglais `eng` doit être installé localement. Pour le français, utiliser `fra+eng` et vérifier la présence des deux modèles. Aucun téléchargement silencieux n'est effectué.

## Tests et limites

Les tests créent réellement des PDF synthétiques rasterisés. Ils contrôlent un tableau de **12 cellules éditables**, un PDF mixte dont le tableau appartient à la **page 2**, la sortie XLSX, la non-altération de la source, l'absence de formules exécutables, la compatibilité du mode historique, la CLI, le routage de l'interface et le refus d'une page OCR sans tableau.

La reconnaissance OCR, la segmentation géométrique et la fidélité visuelle ne sont **pas certifiées**. Un scan complexe, un tableau fusionné, un document incliné ou une mauvaise reconnaissance peut conduire à un refus ou à des valeurs incorrectes. Une vérification humaine reste nécessaire. Aucune capture graphique humaine Windows ni corpus métier indépendant n'est revendiqué.

## Fichiers

- `03-Sources/openpdf_ocr_office_pipeline_v511.py` : option `table_mode`, compte de feuilles, CLI `--editable-tables`.
- `03-Sources/openpdf_operations.py` : priorité au routage OCR lorsque les deux options sont sélectionnées.
- `03-Sources/openpdf_desktop.py` : activation des deux cases avec avertissement.
- `04-Tests-et-Qualification/test_ocr_office_tables_v531.py` : tests fonctionnels.
- `.github/workflows/office-ocr-v511.yml` : tests Ubuntu et Windows.

**Prochaine priorité :** évaluer des scans métier annotés indépendamment (inclinaison, contraste, cellules fusionnées, multipages), mesurer précision/rappel, qualifier manuellement la GUI Windows et reconstruire les binaires V531.
