# OpenPDF Studio V29.3 — Guide utilisateur et qualification
Auteur : Abdelhalim Talbi.

## Installation Windows
1. Extraire le ZIP dans un répertoire accessible en écriture.
2. Exécuter `BUILD-WINDOWS-INSTALLER.cmd` (Python 3.12, pip, PyInstaller, Inno Setup).
3. Installer `installer\OpenPDF-Studio-V29.3-Setup.exe` sur un poste Windows de test.
4. Démarrer OpenPDF Studio depuis le menu Démarrer.

## Utilisation
Utiliser les fonctions de l'interface pour ouvrir les PDF, fusionner plusieurs documents, extraire des pages, compresser et convertir. Contrôler le document produit avant de remplacer les originaux.

## Qualification
- `QUALIFY-WINDOWS-V29.3.cmd` : démarrage et capture réelle de la fenêtre depuis le binaire construit.
- `QUALIFY-UI-V29.3.cmd` : audit des widgets Tk réellement instanciés, commandes et état des contrôles. Rapport `qualification-ui-v29.3.json`. **Ne clique pas sur les commandes et ne valide pas leur fonctionnement.**
- `QUALIFY-INSTALLER-V29.3.cmd` : uniquement VM jetable sans installation existante. La procédure peut installer/désinstaller l'application.
- Les tests Python et l'audit Tk ne remplacent pas une recette fonctionnelle complète des boutons dans le binaire installé.
