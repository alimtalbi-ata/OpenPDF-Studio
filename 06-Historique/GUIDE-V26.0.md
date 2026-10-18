# OpenPDF Studio V26.0 — Application de bureau Windows

Auteur : Abdelhalim Talbi

## Démarrage Windows
Installer Python 3.10+ avec Tkinter. Dans un terminal ouvert dans le dossier extrait :

```powershell
py -3 -m pip install -r requirements-windows-v260.txt
```

Double-cliquer `LANCER-OPENPDF-STUDIO.cmd`. Le programme fonctionne localement.

## Création d’un véritable .exe Windows
Sur **Windows**, double-cliquer `BUILD-WINDOWS-EXE.cmd` (Python et accès à pip requis). Résultat attendu : `dist\OpenPDF-Studio\OpenPDF-Studio.exe`. Cette archive fournit les **sources et scripts de construction**, pas un EXE Windows précompilé.

## Fonctions disponibles
Fusion de plusieurs PDF, découpage page par page, optimisation sans perte (gain non garanti), extraction TXT, export texte éditable vers Word, lignes vers Excel et texte par page vers PowerPoint. Les conversions Office **ne reconstruisent pas** fidèlement tableaux, images et mise en page. Les PDF numérisés sans couche texte nécessitent un OCR non inclus. Les PDF chiffrés sont refusés.

## Qualification
Tests du moteur PDF sur Linux. **Exécution native Windows, compilation PyInstaller, captures réelles Windows non effectuées** dans cet environnement. Les captures Linux des versions précédentes restent identifiées comme telles.

## Sécurité
Traitement local, pas de téléversement, sources jamais écrasées par les opérations PDF. Une confirmation précède l'écrasement de la sortie dans l'interface. Sauvegardez vos documents avant utilisation.
