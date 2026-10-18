# OpenPDF Studio V29.6 — Guide Windows
Auteur : Abdelhalim Talbi

## Construction
Extraire le ZIP sous Windows x64, puis lancer `BUILD-WINDOWS-INSTALLER.cmd`. Le script installe Python 3.12 et les dépendances de construction lorsque nécessaires, exécute les tests, puis génère un dossier d’application, un exécutable portable onefile et un installateur Inno Setup. Accès réseau et winget nécessaires si les dépendances ne sont pas installées.

## Sorties attendues
- `installer/OpenPDF-Studio-V29.6-Setup.exe`
- `portable/OpenPDF-Studio-Portable-V29.6.exe`

## Architecture
`openpdf_commands_v296.py` isole les opérations fusion/extraction/compression de Tkinter et fournit des résultats structurés. Le point d'entrée instancie ce service, mais les anciennes commandes UI ne sont **pas encore toutes migrées**.

## Limites de qualification
Tests Python et opérations PDF exécutables sur Linux. Compilation native, interface réelle, antivirus, démarrage de l'EXE portable, installateur et captures Windows doivent être testés sur Windows. Aucun binaire Windows précompilé n'est livré dans cette archive.
