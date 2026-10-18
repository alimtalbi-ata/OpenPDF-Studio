# OpenPDF Studio V27.7 — Guide utilisateur et compilation

Auteur : Abdelhalim Talbi.

## Utilisation
Lancer `openpdf_windows_v277.py` dans un environnement avec les dépendances de `requirements-windows-v260.txt`. Ajouter des documents avec **Ajouter**, puis utiliser **Fusionner**, **Compresser** ou **Découper**. La barre de progression affiche l’état du traitement ; **Annuler** demande l’arrêt coopératif.

## Compilation Windows
Depuis Windows 10/11 64 bits, lancer `BUILD-WINDOWS-INSTALLER.cmd`. La machine de compilation nécessite une connexion réseau et `winget` si Python ou Inno Setup sont absents. Le script installe les dépendances de compilation, lance les tests et tente de produire `installer\OpenPDF-Studio-V27.7-Setup.exe`. Consulter `build-v27.7.log` en cas d’échec. Le programme final n'exige pas Python.

## Limitations
Cette version conserve encore la chaîne d'héritage graphique V26.x. La barre de commandes est unifiée au niveau visible mais le nettoyage interne des widgets hérités est transitoire. Le Setup.exe n'a pas été compilé ni exécuté sur Windows dans cet environnement. Les conversions éditables héritées doivent faire l'objet d'une recette dédiée.
