# OpenPDF Studio V30.5 — Guide utilisateur
Auteur : Abdelhalim Talbi

## Recherche rapide des actions
Dans la fenêtre principale, appuyer sur **Ctrl+K** ou ouvrir **Recherche > Rechercher une action**.
Saisir une fonction, un format ou une catégorie : les résultats se filtrent immédiatement, sans distinction de casse ni d’accents.
Sélectionner une action et appuyer sur Entrée, double-cliquer ou cliquer sur Exécuter. Échap ferme la fenêtre.
**F6** ouvre toujours l’espace de travail de la V30.4.

## Création des exécutables Windows
Sur Windows x64, lancer `BUILD-WINDOWS-INSTALLER.cmd` dans le répertoire extrait. Le script prépare l'environnement Python, teste le code, construit l'application et l'EXE portable avec PyInstaller, puis l'installateur avec Inno Setup. Une connexion Internet peut être nécessaire.

## Limites
Les conversions texte Word, Excel et PowerPoint ne garantissent pas la fidélité graphique des documents PDF. La compilation et les captures réelles Windows restent à qualifier sur une VM Windows.
