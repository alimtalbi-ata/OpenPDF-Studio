# OpenPDF Studio V30.0 — Guide utilisateur et construction
Auteur : Abdelhalim Talbi.

## Opérations principales
Ouvrir l'application, sélectionner les fichiers PDF, puis utiliser Fusionner, Extraire ou Compresser. Choisir un fichier de sortie distinct de tous les fichiers sources. La V30.0 empêche les collisions source/destination, y compris par alias de chemin ou lien symbolique.

## Construction Windows 64 bits
Depuis le dossier extrait, exécuter `BUILD-WINDOWS-INSTALLER.cmd`. Le script installe les dépendances Python requises si nécessaire, lance les tests et tente de produire `installer\OpenPDF-Studio-V30.0-Setup.exe` et `portable\OpenPDF-Studio-Portable-V30.0.exe`.

## Limites
La V30.0 améliore la sécurité du routage PDF. La refonte complète de l'UI et des conversions Office reste en cours. Aucun exécutable Windows n'a été compilé dans l'environnement Linux de livraison.
