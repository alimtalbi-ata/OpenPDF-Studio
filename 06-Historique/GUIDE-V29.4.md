# OpenPDF Studio V29.4 — Windows
Auteur : Abdelhalim Talbi

1. Décompresser dans un dossier local Windows.
2. Lancer `BUILD-WINDOWS-INSTALLER.cmd` (connexion Internet nécessaire à l’installation des outils manquants).
3. Résultats attendus : `installer\OpenPDF-Studio-V29.4-Setup.exe` et `portable\OpenPDF-Studio-Portable-V29.4.exe`.
4. Portable : copier **uniquement** `OpenPDF-Studio-Portable-V29.4.exe` sur un poste Windows x64 compatible. Aucun Python à installer sur ce poste.
5. Alternative : `BUILD-WINDOWS-EXE.cmd` produit la distribution `dist\OpenPDF-Studio` et l’EXE portable, sans Inno Setup.
6. Qualification réelle : exécuter les scripts `QUALIFY-WINDOWS-V29.4.cmd`, `QUALIFY-UI-V29.4.cmd` ; tester l’installateur exclusivement sur une VM dédiée.

Le mode portable extrait ses dépendances dans un dossier temporaire à chaque lancement. Prévoir l’antivirus et la signature du code. Les résultats de compilation et de lancement Windows ne peuvent être attestés avant exécution sur Windows.
