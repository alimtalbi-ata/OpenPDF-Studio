# OpenPDF Studio V29.0 — Windows
Auteur : Abdelhalim Talbi

## Build automatisé
Lancer `BUILD-WINDOWS-INSTALLER.cmd` dans une console Windows. Les dépendances sont installées dans `.venv`.

## Recette
`QUALIFY-WINDOWS-V29.0.cmd` vérifie le démarrage graphique.
`QUALIFY-INSTALLER-V29.0.cmd` lance **une véritable installation puis désinstallation** : à utiliser uniquement dans une **VM Windows jetable** sans OpenPDF Studio déjà installé. Le script refuse la recette si l'identifiant d'application est déjà enregistré dans HKCU ou HKLM (vues 32/64 bits). La recette reste désactivée par défaut côté Python sans `--allow-install-test`.

## Limites
La recette Windows native, les raccourcis, les opérations PDF via GUI et les captures réelles ne sont pas validés sur l'hôte Linux de développement.
