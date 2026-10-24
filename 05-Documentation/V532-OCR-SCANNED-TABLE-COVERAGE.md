# OpenPDF Studio V532 — Couverture des tableaux OCR multipages

**Auteur : Abdelhalim Talbi — 24 octobre 2026**

## Contexte et besoin

La conversion OCR PDF numérisé vers Excel éditable (V531) pouvait réussir avec un tableau sur une page et aucun tableau reconnu sur une autre page numérisée. Une feuille « Texte PDF » conserve le texte reconnu, mais ne garantit pas qu'un tableau ait été extrait sous forme de cellules. Le simple nombre de caractères OCR ne prouve pas la reconnaissance d'une grille.

## Fonctionnalité V532

La commande `03-Sources/openpdf_ocr_office_pipeline_v511.py` retourne désormais :

- `table_pages` : numéros de pages contenant au moins un tableau extrait.
- `scanned_pages_without_tables` : pages détectées comme numérisées mais sans tableau éditable extrait.
- `table_worksheets` : nombre de feuilles de tableaux, vérifié contre l'inventaire géométrique.

Le mode historique reste compatible. Il émet un avertissement pour les pages numérisées non couvertes. Le mode strict est **facultatif** et refuse la publication si une seule page numérisée n'a aucun tableau détecté :

```powershell
python 03-Sources/openpdf_ocr_office_pipeline_v511.py scan.pdf sortie.xlsx --language eng --editable-tables --require-table-each-scanned-page
```

Le moteur utilise le même extracteur de tableaux que le contrôle de fidélité Excel. Il ne déduit jamais la présence d'un tableau du seul volume de texte OCR. Un refus laisse la destination absente et supprime les fichiers temporaires.

## Cinématique technique

```text
PDF source (SHA-256)
   |--> précontrôle pages numérisées
   |--> OCR local (PyMuPDF/Tesseract, modèles installés)
   |--> contrôle des caractères OCR par page
   |--> conversion XLSX temporaire + extraction des tableaux
   |--> audit structure, cellules, formules et SHA-256
   |--> V532 : comparer pages numérisées / pages avec tableaux
            |--> strict + page manquante : refus, aucun XLSX publié
            |--> sinon : avertissement + publication atomique
   |--> reçu : table_pages, scanned_pages_without_tables
```

## Qualification

- **Statique :** compilation Python des fichiers modifiés.
- **Fonctionnelle Linux :** quatre nouveaux tests, dont deux pages scannées avec 24 cellules éditables, refus d'une page de prose en mode strict, maintien de la sortie et avertissement en mode compatible, validation des paramètres.
- **Régressions locales :** tests historiques OCR Office et PDF vers XLSX.
- **CI Windows :** workflow V532 ajouté. Ne pas assimiler une réussite CI à une revue graphique humaine Windows.
- **Limites :** la présence d'un tableau détecté ne prouve pas l'exactitude des caractères, des colonnes, des cellules fusionnées, ni la fidélité visuelle. Les pages mixtes, tableaux inclinés et documents métier doivent être validés indépendamment.

## Stratégie de compatibilité et sécurité

L'option stricte n'est activée que sur demande et uniquement avec `--editable-tables`. Aucun modèle OCR n'est téléchargé implicitement. La source n'est pas modifiée. L'intégrité de la source et du classeur est vérifiée avant publication. Le dépôt principal reste intact, sans fusion automatique.

## Prochaine priorité

V533 : corpus indépendant de tableaux numérisés inclinés, à cellules fusionnées et multipages ; mesure de rappel/precision sur annotations humaines avant toute affirmation de fidélité.
