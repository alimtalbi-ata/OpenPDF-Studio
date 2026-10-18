# OpenPDF Studio V26.8 — Guide Windows

Auteur : Abdelhalim Talbi.

## Compilation
Sur Windows 10/11 x64 avec accès Internet et winget disponible, double-cliquer `BUILD-WINDOWS-INSTALLER.cmd`. Le script prépare un environnement Python isolé, installe les bibliothèques, exécute les tests de base, compile l’application et appelle Inno Setup. Selon les politiques du poste, les installations d’outils peuvent demander une élévation.

L'installateur final est attendu dans `installer/OpenPDF-Studio-V26.8-Setup.exe`. Les bibliothèques Python sont incluses dans le répertoire PyInstaller distribué par Inno Setup.

## Utilisation
Lancer OpenPDF Studio depuis le menu Démarrer. Ajouter des PDF, choisir l’opération dans la barre d’actions (fusion, compression, découpage, édition), puis définir le résultat. Les conversions doivent être validées selon la fidélité des documents sources.

## Limitations de qualification
Cette livraison a été préparée sous Linux : l'EXE, l'installateur et les captures Windows ne sont **pas** validés. L'absence de `winget`, une politique d'entreprise restrictive ou une indisponibilité réseau empêchent l'installation automatique des prérequis. Le script conserve un journal `build-v26.8.log`.
