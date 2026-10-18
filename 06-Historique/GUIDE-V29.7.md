# OpenPDF Studio V29.7 — Guide
Auteur : Abdelhalim Talbi

## Fonctionnalités raccordées
Fusion, extraction de pages et compression passent désormais par `openpdf_ui_bridge_v297.py` puis `PDFCommands` (V29.6), sans modifier les dialogues Tkinter existants ni le moteur transactionnel. Les opérations sont toujours soumises au task runner historique.

## Construire sous Windows
Exécuter `BUILD-WINDOWS-INSTALLER.cmd` dans un dossier extrait. Le script doit générer `installer\OpenPDF-Studio-V29.7-Setup.exe` et `portable\OpenPDF-Studio-Portable-V29.7.exe`. Python 3.12, PyInstaller et Inno Setup sont nécessaires (installation tentée par winget). Le mode portable onefile décompresse temporairement les dépendances au lancement.

## Limites de qualification
Tests du contrôleur et du pont UI sans fenêtre réussis sous Linux; aucune compilation Windows ni capture réelle Windows exécutée ici. Les conversions éditables restent dépendantes des moteurs historiques et ne sont pas couvertes par ce pont.
