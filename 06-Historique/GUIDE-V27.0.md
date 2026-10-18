# OpenPDF Studio V27.0 — Guide Windows
Auteur : Abdelhalim Talbi

## Utilisation
Ouvrez l’application, ajoutez vos PDF depuis l’explorateur gauche, sélectionnez une opération dans la barre supérieure puis choisissez la sortie et exécutez. La prévisualisation et l’édition restent accessibles dans l’espace de travail existant. Ctrl+O ajoute des fichiers, Ctrl+S enregistre l’édition.

## Compilation
Sous Windows 64 bits, double-cliquez sur `BUILD-WINDOWS-INSTALLER.cmd` sur une machine connectée disposant de winget. Le script installe les outils de compilation si nécessaire, lance les tests, construit l’application puis l’installateur Inno Setup dans `installer/`. La réussite doit être vérifiée dans `build-v27.0.log`. Les machines sans winget ou sans accès aux dépôts ne sont pas encore prises en charge.

## Qualification
Tests unitaires sans interface exécutables sur Linux ; génération réelle d’EXE, installation, désinstallation et captures Windows non vérifiées dans cet environnement.
