# OpenPDF Studio V26.7 — Guide Windows

Auteur : Abdelhalim Talbi

## Lancement
1. Installer Python 3.11+ et le lanceur `py`.
2. Exécuter `py -3 -m pip install -r requirements-windows-v260.txt`.
3. Double-cliquer sur `LANCER-OPENPDF-STUDIO.cmd`.

## Interface
La barre d’actions rapide donne accès à l’ajout de PDF, à l’édition des pages, à l’enregistrement et aux opérations de fusion, compression et découpage. L’explorateur de gauche permet de sélectionner les fichiers. Le panneau Propriétés analyse le document en arrière-plan, sans figer la fenêtre pendant la lecture des métadonnées.

## Construire un exécutable sur Windows
Exécuter `BUILD-WINDOWS-EXE.cmd` sur une machine Windows disposant de Python et d’Internet pour installer les dépendances. Le résultat attendu est `dist\OpenPDF-Studio\OpenPDF-Studio.exe` (distribution *onedir*). Le script n’est pas un exécutable précompilé. La compilation et l’exécution sur Windows doivent être validées localement.

## Limites
Les conversions Office sont principalement textuelles ; elles ne garantissent pas une restitution fidèle des mises en page. La lecture et le rendu des pages de l’éditeur restent synchrones pour certains usages et les documents très volumineux peuvent provoquer des pauses. Ne pas remplacer un PDF source sans sauvegarde.
