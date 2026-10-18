# OpenPDF Studio V28.6 — qualification Windows

Auteur : Abdelhalim Talbi.

## Génération
Sur Windows 10/11 x64, extraire le ZIP puis lancer `BUILD-WINDOWS-INSTALLER.cmd`. La commande installe les outils nécessaires si winget est disponible, lance les tests, construit `dist\OpenPDF-Studio\OpenPDF-Studio.exe` avec PyInstaller et `installer\OpenPDF-Studio-V28.6-Setup.exe` avec Inno Setup. Pour compiler uniquement l’application : `BUILD-WINDOWS-EXE.cmd`.

## Qualification réelle
Lancer `QUALIFY-WINDOWS-V28.6.cmd` après compilation, dans une session Windows interactive. La vérification attend une **fenêtre visible** portant le titre OpenPDF Studio, et non seulement un processus en vie. Un JSON est enregistré dans `qualification-windows-v28.6.json`; une capture du bureau peut être enregistrée dans `captures/windows-v28.6-real.png`. La présence de la fenêtre ne prouve pas le bon fonctionnement des fonctions métier.

## Limites de la qualification fournie
La compilation Windows native, la validation de l'installateur et l'utilisation GUI ne sont pas exécutables dans l'environnement Linux de préparation. Aucun `Setup.exe` Windows précompilé ni aucune capture réelle Windows n'est inclus. Les tests statiques ne valent pas une qualification de production.

## Recette manuelle complémentaire
Installer le Setup, lancer l'application, ouvrir deux PDF, fusionner, découper, compresser, vérifier les pages et contenus, tester l'annulation, fermer, désinstaller et vérifier les raccourcis. Archiver les journaux et captures.
