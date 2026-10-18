# OpenPDF Studio V31.0 — Guide utilisateur
Auteur : Abdelhalim Talbi

## Conversion depuis le bouton principal
1. Ajouter un seul fichier PDF existant.
2. Choisir PDF vers Word, Excel, PowerPoint ou Extraire le texte.
3. Sélectionner la destination avec l’extension attendue.
4. Cliquer **Exécuter**. Le chemin utilise maintenant le même contrôleur transactionnel que les actions directes.
5. Confirmer le remplacement si la destination existe.

Les autres opérations (fusion, découpe, compression) conservent leur comportement antérieur.

## Compilation Windows
Lancer `BUILD-WINDOWS-INSTALLER.cmd` depuis le dossier extrait. Le script prépare Python, les dépendances, les tests, l'EXE portable et l'installateur Inno Setup. Compilation et installation natives non testées dans cet environnement Linux.
