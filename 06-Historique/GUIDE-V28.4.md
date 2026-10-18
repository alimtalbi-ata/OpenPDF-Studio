# OpenPDF Studio V28.4 — Guide Windows
Auteur : Abdelhalim Talbi.

1. Sur Windows 10/11 x64, extraire toute l’archive dans un dossier accessible en écriture.
2. Lancer `BUILD-WINDOWS-INSTALLER.cmd` (connexion Internet nécessaire pour les dépendances). Il installe Python 3.12 et Inno Setup via winget s’ils manquent.
3. Vérifier `build-v28.4.log`, `dist\OpenPDF-Studio\OpenPDF-Studio.exe` et `installer\OpenPDF-Studio-V28.4-Setup.exe`.
4. Exécuter `QUALIFY-WINDOWS-V28.4.cmd` sur Windows pour vérifier le démarrage pendant 5 secondes et produire `qualification-windows-v28.4.json`.
5. Tester manuellement ouverture, fusion, découpage, compression, export, fermeture et désinstallation ; joindre des captures réelles et les journaux.

**Attention :** la présence de fichiers EXE et un lancement de 5 secondes ne prouvent pas toutes les fonctions ni la réussite de l’installation/désinstallation. La qualification complète doit être réalisée sur Windows.
