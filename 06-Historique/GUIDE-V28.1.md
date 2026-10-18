# OpenPDF Studio V28.1 — Guide Windows
Auteur : Abdelhalim Talbi

## Génération de l’application
Sur Windows 10/11 x64, extraire le ZIP dans un dossier accessible en écriture. Lancer `BUILD-WINDOWS-EXE.cmd` pour produire `dist\OpenPDF-Studio\OpenPDF-Studio.exe` (conserver tout le dossier `dist\OpenPDF-Studio`).

## Génération de l’installateur
Lancer **uniquement** `BUILD-WINDOWS-INSTALLER.cmd` pour produire l'application et `installer\OpenPDF-Studio-V28.1-Setup.exe`. Le script installe dans un environnement virtuel les dépendances de compilation et utilise winget pour Python 3.12 et Inno Setup si absents. Winget et un accès réseau sont requis si ces outils manquent. Consulter `build-v28.1.log` en cas d'échec.

## Qualification sur Windows (à exécuter)
1. Compiler le Setup, contrôler sa taille et sa signature éventuelle (non signée par défaut).
2. Installer sous un compte standard (élévation éventuellement requise), ouvrir le raccourci.
3. Tester ouverture, fusion, extraction, compression avec PDF valide, invalide, protégé, destination existante et annulation.
4. Fermer et rouvrir l'application, désinstaller et vérifier les raccourcis.
5. Prendre des captures **réelles** des écrans et consigner les résultats.

## Limites
Aucun test de compilation/installation/exécution de l'interface sur Windows n'a été effectué dans l'environnement Linux de production de ce ZIP. La compilation Python et les tests unitaires ne remplacent pas la recette Windows.
