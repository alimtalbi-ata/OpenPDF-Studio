# OpenPDF Studio V29.9 — guide Windows
Auteur : Abdelhalim Talbi.

## Compilation
Extraire le ZIP sous Windows x64, puis lancer `BUILD-WINDOWS-INSTALLER.cmd`. Le script installe les dépendances de build, exécute les tests, génère une application onedir, un portable onefile et l’installateur Inno Setup.

## Utilisation
Dans l’interface, sélectionner une opération (fusion, découpage, compression), les PDF source puis la destination. Une tâche affiche la progression et peut être annulée. Les opérations refusent les entrées invalides et publient les résultats de manière atomique.

## Validation
`QUALIFY-PORTABLE-V29.8.cmd` reste historique; utiliser les scripts `QUALIFY-PORTABLE-V29.9.cmd`, `QUALIFY-WINDOWS-V29.9.cmd`, et vérifier le rapport généré sur Windows.

La fidélité des conversions Word/Excel/PowerPoint est limitée par les bibliothèques existantes; aucune garantie de reconstruction de mise en page.
