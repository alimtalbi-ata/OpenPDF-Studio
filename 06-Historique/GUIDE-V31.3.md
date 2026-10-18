# OpenPDF Studio V31.3 — Guide utilisateur

Auteur : Abdelhalim Talbi.

## Accueil et actions courantes

Les actions principales restent Fusionner, Compresser, Découper et Vers Word. Le bouton **Vers Word** ouvre désormais un parcours guidé : choisir un PDF, sélectionner la destination DOCX proposée automatiquement, puis valider le lancement. Le bouton Annuler de chaque sélecteur interrompt le parcours sans modifier le fichier cible. La conversion est traitée par le moteur transactionnel de V30.9.

Pour les autres actions, les contrôles et menus historiques restent disponibles. Raccourci Word : Ctrl+Maj+W.

## Construction Windows

Exécuter `BUILD-WINDOWS-INSTALLER.cmd` sur Windows avec accès aux dépendances. Le script vérifie les tests, construit une version installable et un EXE portable PyInstaller. Les résultats de compilation et le lancement réel doivent être qualifiés sur Windows.

## Limites

Conversion Word textuelle, fidélité de mise en page non garantie. L'annulation du contrôleur est coopérative, pas une interruption forcée du moteur PDF.
