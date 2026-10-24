# OpenPDF Studio — Sources actives V40.3

Auteur : Abdelhalim Talbi

## Points d'entrée
- `openpdf_studio.py` : lancement de l'application Windows et autotests.
- `openpdf_desktop.py` : interface utilisateur Tkinter.
- `openpdf_operations.py` : façade d'exécution des opérations.
- `openpdf_atomic_output.py` : publication exclusive sans écrasement.
- `openpdf_page_service_v345.py` : fusion, extraction, réorganisation, découpage.
- `openpdf_conversion_service_v351.py` : conversion Office avec audit.
- `openpdf_ocr_service_v347.py` : OCR hors ligne, dépendant de Tesseract.

## Compiler sous Windows
Depuis la racine du dépôt, exécuter `02-Compilation\\BUILD-WINDOWS-INSTALLER.cmd`.
La version est lue dans `VERSION.txt`. Les binaires produits se trouvent dans
`01-Application\\binary` après validation. La compilation installe ses
dépendances de build dans un environnement Python isolé ; l'utilisateur final
n'a pas besoin du code source ni de Python pour lancer les exécutables.

## Qualification
`02-Compilation\\VERIFY-WINDOWS-RELEASE.ps1` contrôle la présence des
artefacts et les preuves de qualification. GitHub Actions exécute aussi
les tests de sécurité et les tests Windows. Cela ne remplace pas une recette
sur une machine Windows indépendante.

## Historique
Les fichiers suffixés de versions anciennes sont conservés pour compatibilité
et audit. Ils ne doivent pas être supprimés sans cartographie des imports.
La documentation d'architecture est dans
`05-Documentation/AUDIT-ARCHITECTURE-ET-ROADMAP-V40.2.md`.
