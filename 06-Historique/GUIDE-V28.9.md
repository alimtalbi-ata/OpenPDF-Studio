# OpenPDF Studio V28.9 — Guide de qualification Windows

Auteur : Abdelhalim Talbi.

1. Extraire l’archive sur Windows x64.
2. Exécuter `BUILD-WINDOWS-INSTALLER.cmd` pour générer l’EXE et l’installateur.
3. Exécuter `QUALIFY-WINDOWS-V28.9.cmd` pour contrôler la fenêtre de l’application.
4. Sur une VM Windows de test **sans installation préexistante**, exécuter `QUALIFY-INSTALLER-V28.9.cmd`. L’installateur Inno Setup conserve le même AppId que les versions précédentes ; ne pas lancer une recette silencieuse sur un poste de production : elle pourrait affecter une installation déjà enregistrée.
5. Examiner les journaux et les rapports JSON.

Les tests exécutés sous Linux ne remplacent pas la compilation, l’installation et la validation visuelle sous Windows. Aucune capture réelle Windows n’est fournie.
