# OpenPDF Studio V27.6 — Guide utilisateur et compilation
Auteur : Abdelhalim Talbi.

## Utilisation
Lancer `openpdf_windows_v276.py` avec les dépendances du projet, ou l’application compilée sous Windows. La barre unique propose Ajouter, Éditer les pages, Enregistrer, Fusionner, Compresser et Découper. Pendant un traitement PDF, ces commandes sont temporairement bloquées. La progression et l’annulation restent accessibles dans la zone d’état héritée V27.3.

## Construction Windows
Depuis Windows, exécuter `BUILD-WINDOWS-INSTALLER.cmd` dans le dossier extrait. Le script installe les outils de compilation lorsque winget est disponible, exécute les tests, puis produit `installer\OpenPDF-Studio-V27.6-Setup.exe` via PyInstaller et Inno Setup. Une connexion Internet et des droits appropriés peuvent être nécessaires sur la machine de compilation. L’utilisateur final n’a pas besoin de Python.

## Qualification
Les tests de routage de commandes sont indépendants de l’interface. Compilation de l’EXE, installation, désinstallation et captures réelles Windows non vérifiées dans cet environnement Linux.
