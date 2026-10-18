# OpenPDF Studio V39.9 — compilation Windows native

1. Extraire le ZIP complet sur Windows 10/11 x64, chemin sans caractères spéciaux.
2. Depuis la racine, exécuter `02-Compilation\BUILD-WINDOWS-INSTALLER.cmd`.
3. Les sorties validées sont placées dans `01-Application\binary`.
4. La CI GitHub Actions utilise un runner Windows 2022; le dépôt doit contenir l’arborescence extraite à sa racine.
5. En cas d’échec, examiner `01-Application\binary\build-v39.9.log` et ne pas publier les anciens exécutables comme nouveaux.
6. Les tests UI interactifs et la compatibilité antivirus restent à qualifier manuellement.

La CI est fournie mais n'a PAS été exécutée depuis cet environnement Linux. Aucun EXE n'est livré sans build Windows réel.
