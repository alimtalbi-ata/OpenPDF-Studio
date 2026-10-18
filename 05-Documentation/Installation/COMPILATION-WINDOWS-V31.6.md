# Installation et compilation Windows V31.6

1. Extraire l'archive dans un dossier local Windows avec droits d'écriture.
2. Installer Python Windows compatible avec `requirements-windows-v260.txt`, puis Inno Setup si un installateur est souhaité.
3. Exécuter `BUILD-WINDOWS-INSTALLER.cmd` depuis un terminal Windows. Ce script crée un environnement virtuel, installe les dépendances, exécute les tests et lance PyInstaller puis Inno Setup.
4. Consulter `build-v31.6.log` et les résultats de qualification.
5. Vérifier `dist\OpenPDF-Studio\OpenPDF-Studio.exe`, `portable\OpenPDF-Studio-Portable-V31.6.exe` et `installer\OpenPDF-Studio-V31.6-Setup.exe`.
6. Installer et tester réellement les parcours fusion, découpage, compression et conversion sur une machine Windows vierge.

**Important :** les binaires ne sont pas compilés dans cette archive Linux ; les outils de compilation sont fournis.
