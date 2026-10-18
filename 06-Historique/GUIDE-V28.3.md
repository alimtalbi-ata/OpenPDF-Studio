# OpenPDF Studio V28.3 — Guide Windows
Auteur : Abdelhalim Talbi

## Générer l’application EXE
Sur Windows 10/11 x64 avec accès réseau, lancer `BUILD-WINDOWS-EXE.cmd`. Le résultat attendu est `dist\OpenPDF-Studio\OpenPDF-Studio.exe` accompagné du répertoire `_internal` ; distribuer le dossier complet, pas uniquement le fichier EXE.

## Générer l’installateur
Lancer `BUILD-WINDOWS-INSTALLER.cmd`. Le script recherche ou installe Python 3.12 et Inno Setup via winget, crée `.venv`, installe les dépendances, exécute les tests et compile le programme puis le Setup. Résultat attendu : `installer\OpenPDF-Studio-V28.3-Setup.exe`. Vérifier `build-v28.3.log` en cas d’échec. Connexion réseau, droits et winget peuvent être nécessaires.

## Recette manuelle Windows obligatoire
Installer le Setup sur une VM Windows propre, démarrer l’application, ouvrir un PDF, fusionner, extraire, compresser, vérifier les fichiers de sortie, fermer et désinstaller. Vérifier la présence des dépendances, les raccourcis, les journaux, et capturer des screenshots réels. Les contrôles statiques ne remplacent pas cette recette.
