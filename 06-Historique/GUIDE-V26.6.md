# OpenPDF Studio V26.6 — Guide Windows

Auteur : Abdelhalim Talbi.

## Lancement
Installer les dépendances de `requirements-windows-v260.txt` avec `py -3 -m pip install -r requirements-windows-v260.txt`, puis double-cliquer sur `LANCER-OPENPDF-STUDIO.cmd`.

## Interface
L’explorateur latéral affiche les PDF chargés. Double-cliquer pour ouvrir le document dans l’éditeur intégré. Le séparateur entre explorateur et zone de travail est redimensionnable. Les fonctions de traitement PDF restent dans la zone principale ; les onglets d’édition et propriétés se trouvent sous celle-ci.

Raccourcis : Ctrl+O ajoute des fichiers ; Ctrl+S enregistre le document modifié si un document est ouvert ; Ctrl+Entrée lance l’opération choisie.

## Qualification
Les tests automatiques Linux ne remplacent pas les tests natifs Windows. Aucun exécutable compilé ni capture native Windows n’est fourni. Les PDF volumineux doivent encore faire l’objet de tests de performance réels.
