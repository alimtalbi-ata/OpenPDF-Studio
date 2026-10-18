# OpenPDF Studio V27.1 — Guide technique et utilisateur
Auteur : Abdelhalim Talbi.

## Utilisation
Lancer le point d’entrée `openpdf_windows_v271.py` avec les dépendances Windows. Les actions historiques de l’interface restent disponibles.

## Moteur indépendant
`openpdf_engine_v271.py` expose `merge_pdfs` et `extract_pages`. Les sorties sont écrites dans un fichier temporaire situé sur le même volume puis remplacées atomiquement. Une source ne peut pas être écrasée par sa propre sortie.

## Exécution asynchrone
`openpdf_tasks_v271.py` retourne des futures ; seul le thread Tk doit manipuler les widgets. L’intégration complète des commandes GUI au moteur indépendant reste à faire.

## Windows
Double-cliquer `BUILD-WINDOWS-INSTALLER.cmd` sur une machine Windows équipée de winget et d’un accès réseau. La compilation réelle et l’installation ne sont pas validées dans cet environnement Linux.

## Captures
Aucune capture réelle de l’interface Windows V27.1 n’a été produite. Les captures historiques ne doivent pas être présentées comme V27.1.
