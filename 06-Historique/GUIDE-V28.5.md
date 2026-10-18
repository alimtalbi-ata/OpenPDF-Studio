# OpenPDF Studio V28.5 — Guide de compilation et qualification Windows
Auteur : Abdelhalim Talbi

## Génération en un clic
Sur Windows 10/11 x64, extraire le ZIP puis lancer `BUILD-WINDOWS-INSTALLER.cmd`. Le script recherche/installe Python 3.12 et Inno Setup via winget, crée `.venv`, installe les bibliothèques, exécute les tests, puis PyInstaller et Inno Setup. Une connexion Internet et winget peuvent être nécessaires. Les permissions d'installation peuvent être demandées par Windows.

Sorties attendues : `dist\OpenPDF-Studio\OpenPDF-Studio.exe` (avec son répertoire `_internal`) et `installer\OpenPDF-Studio-V28.5-Setup.exe`. Ne pas déplacer l'EXE seul : le mode `onedir` nécessite `_internal`.

## Recette réelle Windows
Exécuter `QUALIFY-WINDOWS-V28.5.cmd` après compilation. Ce script vérifie la structure de l'EXE, le lance pendant six secondes, le ferme, et écrit `qualification-windows-v28.5.json`. Avec Pillow installé par le script de build et une session graphique interactive ouverte, une capture réelle du bureau est écrite dans `captures\windows-v28.5-real.png`. La capture ne garantit pas à elle seule que la fenêtre est visible.

Tester manuellement : démarrage, ajout PDF, fusion, extraction, compression, export, messages d'erreur, installation/désinstallation et suppression des fichiers temporaires. Joindre les journaux de compilation et rapports de recette.

## Limites
Les tests Python exécutés sur Linux ne valident ni la compilation PE Windows, ni les opérations de l'installateur, ni la visibilité de la fenêtre Tk. Aucun `Setup.exe` natif Windows ni capture réelle Windows ne sont fournis dans cette archive de sources.
