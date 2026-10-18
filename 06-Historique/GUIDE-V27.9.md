# OpenPDF Studio V27.9 — Guide utilisateur
Auteur : Abdelhalim Talbi

## Utilisation
Ouvrir un PDF avec Ctrl+O ; enregistrer avec Ctrl+S. Fusionner : Ctrl+Maj+M ; compresser : Ctrl+Maj+C ; extraire : Ctrl+Maj+D. Choisir un fichier de destination différent du document source. Attendre la fin du traitement avant de fermer l’application.

## Installation Windows
Extraire le ZIP dans un chemin local puis exécuter `BUILD-WINDOWS-INSTALLER.cmd`. Ce script installe les outils de construction disponibles via winget si nécessaire, crée un environnement Python isolé, lance les tests, génère le programme PyInstaller puis compile l’installateur Inno Setup. Connexion Internet et winget nécessaires pour l’amorçage automatique. Exécuter ensuite `installer\OpenPDF-Studio-V27.9-Setup.exe`. L'utilisateur final n'a pas besoin de Python.

## V27.9
La boucle de rafraîchissement des commandes est maintenant gérée par un seul planificateur annulé à la fermeture normale. Cette version conserve encore des classes graphiques héritées : la refonte complète est à poursuivre.
