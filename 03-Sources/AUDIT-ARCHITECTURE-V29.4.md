# Audit OpenPDF Studio V29.4
Auteur : Abdelhalim Talbi

## Constat principal
L’interface est composée de **34 modules de versions successives**, avec des classes héritées et des surcharges successives. Cela accroît le couplage, les effets de bord et la complexité des tests. Voir le rapport JSON pour l’inventaire AST des classes, méthodes et fonctions du moteur.

## Interactions et risques
- UI → contrôleurs → moteur PDF : vérifier que la sélection de fichiers, l’ordre, la destination et le mode d’opération sont cohérents.
- Traitements longs : vérifier les mises à jour Tkinter exclusivement depuis le thread UI, la gestion d’annulation et les erreurs.
- Conversion PDF → Word/Excel/PowerPoint : le texte est éditable, mais la restitution des tableaux et de la mise en page reste limitée.
- Compression : les gains dépendent du contenu et peuvent être nuls.
- Sécurité : ne jamais écraser silencieusement la source ; contrôler les chemins, les fichiers corrompus et les permissions.

## Décisions de packaging
- Installateur Windows : Inno Setup + distribution PyInstaller `onedir`, robustesse et désinstallation native.
- Portable Windows : PyInstaller `--onefile`, **un seul fichier EXE distribué**. Les DLL et bibliothèques sont extraites temporairement à l’exécution.
- `BUILD-WINDOWS-INSTALLER.cmd` construit les deux formats avec un seul lancement. `BUILD-WINDOWS-EXE.cmd` construit les exécutables sans installateur.
- Pas d’exécutable Windows compilé dans cette archive : la compilation doit être exécutée sur Windows.

## Limites de qualification
Audit AST et tests Python exécutables ici ; les interactions UI, la capture de fenêtres, les binaires PE générés et l’installation Windows nécessitent une VM Windows. Aucune capture réelle Windows n’est revendiquée.
