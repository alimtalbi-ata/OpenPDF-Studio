# OpenPDF Studio V29.5 — Windows
Auteur : Abdelhalim Talbi.

## Construction
Exécuter `BUILD-WINDOWS-INSTALLER.cmd` depuis un poste Windows x64 avec réseau et droits pour installer les outils. Le script construit `dist\OpenPDF-Studio\OpenPDF-Studio.exe`, `portable\OpenPDF-Studio-Portable-V29.5.exe` (onefile) et `installer\OpenPDF-Studio-V29.5-Setup.exe`. Les binaires Windows ne sont pas inclus dans l’archive source.

## Qualification
`QUALIFY-WINDOWS-V29.5.cmd`, `QUALIFY-UI-V29.5.cmd` et `QUALIFY-PORTABLE-V29.5.cmd`. L’audit UI inventorie aussi les commandes sans action et les libellés dupliqués. Le test portable vérifie la présence et la tenue du processus pendant 20 s : il ne valide pas toutes les opérations PDF.

## Limites
PyInstaller onefile extrait temporairement des bibliothèques. Le démarrage peut être plus lent. La validation native Windows, les captures et les tests E2E des boutons restent à réaliser sur VM Windows. Ne jamais exécuter la qualification installateur sur une machine de production.
