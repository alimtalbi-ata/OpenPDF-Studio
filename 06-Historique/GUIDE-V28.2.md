# OpenPDF Studio V28.2 — Guide et recette
Auteur : Abdelhalim Talbi

## Génération Windows
Double-cliquer `BUILD-WINDOWS-INSTALLER.cmd` sur Windows 10/11 x64 avec connexion Internet, droits pour installer les outils et winget disponible. Le script installe Python 3.12 et Inno Setup si nécessaires, prépare les dépendances Python, exécute les tests et la recette PDF réelle, compile `dist\OpenPDF-Studio\OpenPDF-Studio.exe`, puis `installer\OpenPDF-Studio-V28.2-Setup.exe`.

`BUILD-WINDOWS-EXE.cmd` construit seulement l'application. Conserver tout le dossier `dist\OpenPDF-Studio` : l'exécutable n'est pas un fichier autonome onefile.

## Recette fonctionnelle
`python openpdf_functional_v282.py` génère des PDF temporaires, valide fusion, extraction, compression, annulation, non-corruption des sorties existantes et intégrité des sources. Les fichiers temporaires sont nettoyés.

## Limites
La compilation réelle sous Windows, l'installation, le lancement graphique, la désinstallation et les captures Windows ne sont pas qualifiés depuis cet environnement Linux. Le build nécessite winget et accès aux dépôts ; il ne s'agit pas d'un installeur hors-ligne.
