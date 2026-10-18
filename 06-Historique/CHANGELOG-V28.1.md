# V28.1 — Audit du packaging Windows
Auteur : Abdelhalim Talbi
- BUILD-WINDOWS-EXE.cmd n'utilise plus l'ancien point d'entrée V26.7 : délégation au pipeline unique V28.1.
- Génération EXE seule (`--exe-only`) ou EXE + Setup à partir d'un script central.
- Python 3.12 isolé, contrôle des erreurs et tests avant packaging.
- Audit statique des contrats de compilation et tests automatisés.
- Recette Windows détaillée ; aucune prétention de validation native Windows.
