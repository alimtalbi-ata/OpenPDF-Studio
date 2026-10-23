# OpenPDF Studio V51.1 — OCR hors ligne et conversion Office éditable

**Auteur : Abdelhalim Talbi — 23 octobre 2026.**

## Objectif et portée

V51.1 transforme le blocage préventif des scans introduit en V51.0 en un parcours opérationnel : analyse du PDF, OCR local sélectif, contrôle du texte reconnu et conversion vers DOCX, XLSX ou PPTX contenant du texte éditable. L'OCR n'est déclenché que si le précontrôle détecte au moins une page numérisée. Les pages avec texte natif sont préservées. Le texte exporté est éditable, mais les tableaux, polices, images, positions et mises en page d'origine ne sont pas garantis.

## Utilisation CLI (sources Python ou exécutable intégrant la commande)

`python 03-Sources/openpdf_studio.py --ocr-office facture-scannee.pdf facture.docx --language fra+eng --dpi 200 --min-chars 1`

Remplacer `.docx` par `.xlsx` ou `.pptx` pour les autres formats. Le moteur OCR est **hors ligne** et nécessite les modèles Tesseract correspondants déjà présents sur le système. Aucun téléchargement silencieux n'est effectué. La disponibilité de ces modèles dans le portable Windows autonome n'est pas établie.

## Contrôle de sécurité et d'intégrité

1. Vérification de la source et de la destination, refus des liens symboliques et de l'écrasement.
2. Empreinte SHA-256 de la source et classification des pages avec détection des scans.
3. OCR sélectif dans un dossier temporaire privé et validation de son empreinte.
4. Vérification d'au moins un caractère non blanc sur chaque page initialement classée comme scannée ; seuil configurable. Le nombre de caractères est une mesure de couverture, **pas de justesse de reconnaissance**.
5. Conversion Office par le moteur existant, audit OOXML et contrôle strict du texte éditable, empreinte de sortie.
6. Copie contrôlée sur le volume de destination, nouvelle vérification SHA-256 de la source et publication exclusive. Aucun fichier final n'est publié en cas d'échec avant le commit.

Les reçus contiennent empreintes, compteurs et avertissements ; ils ne recopient pas le texte reconnu. L'opération peut traiter des documents contenant des données sensibles, à protéger selon la politique locale.

## Qualification et limites

- **11 nouveaux tests fonctionnels Linux réussis**, incluant deux OCR réels sur PDF synthétiques (scan seul et document mixte), refus d'une destination existante, absence de modèle, OCR vide, altération de reçu, échec de conversion et nettoyage des temporaires.
- **12 tests V51.0 de régression réussis** sur PDF synthétiques.
- **92 modules dans la fermeture statique**, zéro module manquant.
- Les tests d'OCR réel sont **explicitement ignorés** si le modèle `eng` est absent ; leur succès sous Windows CI ne doit pas être affirmé sans preuve d'exécution.
- CI GitHub V51.1 : tests OCR Office Ubuntu/Windows **PASS** (#40029299618), compression Ubuntu/Windows **PASS** (#40029299518), métadonnées **PASS** (#40029299409). Build Windows natif **2/2 jobs PASS** (#40029299487) : portable, installateur, auto-tests, installation, lancement et désinstallation silencieux. Les reçus et exécutables réels sont intégrés au ZIP cumulatif. La recette graphique humaine reste non réalisée.
- OCR non certifié en précision, conversion texte éditable non fidèle visuellement, aucune signature Authenticode, aucune preuve de conformité PDF/A, d'accessibilité ou d'impression.

## Roadmap V51.2

Parcours GUI Windows guidé OCR → Office avec indicateurs de couverture et avertissements de fidélité, modèles Tesseract embarqués/licenciés et qualifiés, puis corpus métier autorisé (factures, tableaux, formulaires, documents multicolonnes) et mesures CER/WER avec références humaines.
