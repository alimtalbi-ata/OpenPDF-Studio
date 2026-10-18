# OpenPDF Studio V27.8 — Guide Windows
Auteur : Abdelhalim Talbi

## Utilisation
Ouvrir les fichiers via **Ajouter** (Ctrl+O), sélectionner les documents, puis choisir **Fusionner**, **Compresser** ou **Découper**. Le résultat est enregistré à la destination choisie. Une opération en cours désactive les commandes incompatibles ; l’annulation est coopérative.

Raccourcis : Ctrl+O (ajouter), Ctrl+S (enregistrer), Ctrl+Maj+M (fusionner), Ctrl+Maj+C (compresser), Ctrl+Maj+D (découper).

## Construction Windows
Sur Windows, exécuter `BUILD-WINDOWS-INSTALLER.cmd`. Le script prépare un environnement virtuel, installe les dépendances, exécute les tests, compile avec PyInstaller puis construit l'installateur avec Inno Setup. Internet et winget peuvent être nécessaires. Consulter `build-v27.8.log` en cas d'échec. La génération n'a pas été testée sur Windows dans cette livraison.
