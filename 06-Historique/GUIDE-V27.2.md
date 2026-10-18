# OpenPDF Studio V27.2 — Guide
Auteur : Abdelhalim Talbi.

Barre d'actions : **Fusionner**, **Compresser**, **Découper** utilisent maintenant les traitements PDF asynchrones indépendants. Raccourcis Ctrl+Maj+M, Ctrl+Maj+C, Ctrl+Maj+D. La barre de progression est indéterminée (activité), et non un pourcentage réel. L'annulation dans l'interface reste à développer ; le moteur de compression prend en charge une annulation coopérative avant publication du fichier.

Sur Windows, double-cliquer `BUILD-WINDOWS-INSTALLER.cmd` dans le répertoire extrait. Il installe les outils de compilation nécessaires lorsque `winget` est disponible, exécute les tests et tente de créer `installer/OpenPDF-Studio-V27.2-Setup.exe`. Un accès Internet et les droits appropriés peuvent être nécessaires. Aucune compilation Windows n'a été effectuée dans cet environnement.

La compression est sans perte et ne garantit pas une diminution de taille. Les opérations historiques restent présentes pour compatibilité ; la migration de toutes les commandes et la recette Windows complète ne sont pas achevées.
