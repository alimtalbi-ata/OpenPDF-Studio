# OpenPDF Studio V28.8 — Guide Windows
Auteur : Abdelhalim Talbi

1. Extraire l’archive dans un répertoire inscriptible Windows 10/11 x64.
2. Lancer `BUILD-WINDOWS-INSTALLER.cmd` pour installer les dépendances de build, exécuter les tests, compiler le logiciel et l’installateur.
3. Lancer `QUALIFY-WINDOWS-V28.8.cmd` pour vérifier la fenêtre graphique du binaire non installé.
4. Lancer `QUALIFY-INSTALLER-V28.8.cmd` pour installer en silence dans un dossier temporaire isolé, démarrer le logiciel installé et vérifier sa désinstallation.
5. Consulter `qualification-install-v28.8.json` et `build-v28.8.log`. Un statut FAIL signifie que la recette a échoué.

La qualification Windows n’a pas été exécutée dans l’environnement Linux de préparation. Aucun cliché Windows réel n’est fourni. Les tests de l’installateur ne valident pas encore les interactions PDF de l’interface ni tous les raccourcis.
