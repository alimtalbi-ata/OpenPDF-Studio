# OpenPDF Studio V29.2 — Qualification Windows
Auteur : Abdelhalim Talbi

## Compilation et recette
`BUILD-WINDOWS-INSTALLER.cmd` installe les dépendances Python et tente de construire l’EXE et l’installateur sous Windows.
`QUALIFY-WINDOWS-V29.2.cmd` vérifie une fenêtre visible liée au PID et capture **la fenêtre réelle** (rectangle GetWindowRect), sans substituer une maquette. L’échec de capture demandé est bloquant.
`QUALIFY-INSTALLER-V29.2.cmd` est **réservé à une VM Windows jetable**. Il lance d’abord les tests réels du moteur PDF, puis vérifie la présence d’une installation existante avant toute installation. La recette ne constitue pas une automatisation des clics de fusion/conversion dans l’UI.

## Limites
La compilation, l'installation et les captures réelles Windows n'ont pas été exécutées dans l'environnement Linux. Les contrôles du moteur PDF sont distincts des tests GUI.
