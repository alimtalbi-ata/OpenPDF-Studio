# OpenPDF Studio V27.5 — Guide utilisateur et exploitation
Auteur : Abdelhalim Talbi

## Utilisation
Lancer OpenPDF Studio, ajouter les PDF depuis la barre d’outils, puis sélectionner Fusionner, Compresser ou Découper. Les traitements utilisent une barre de progression et un bouton Annuler ; l’annulation est coopérative.

## Diagnostics
Les erreurs d’interface et des tâches PDF sont consignées dans `%LOCALAPPDATA%\OpenPDF-Studio\logs\openpdf.log` sous Windows. Rotation : 2 Mo, trois sauvegardes. Le journal n’enregistre pas le contenu des documents ni les chemins des fichiers d’entrée. Les anciens modules conservent leur propre gestion d’erreurs.

## Construire sous Windows
Exécuter `BUILD-WINDOWS-INSTALLER.cmd` sur une machine Windows disposant d'un accès réseau et de winget si Python/Inno Setup sont absents. Le résultat attendu est `installer\OpenPDF-Studio-V27.5-Setup.exe`. Le script n'a pas été qualifié sur Windows dans cette livraison.

## Limites
L’interface repose encore sur des classes héritées. La compilation et l'installation Windows, les captures réelles et la non-régression globale restent à vérifier.
