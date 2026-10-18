# OpenPDF Studio V30.9 — Guide utilisateur
Auteur : Abdelhalim Talbi

Accès : F6 pour l’espace de travail, Ctrl+K pour rechercher une fonction. Sélectionner le PDF et la destination puis lancer la conversion. Formats DOCX, XLSX, PPTX, TXT : extraction principalement textuelle, sans garantie de reproduction de mise en page.

**Suivi** : phases internes `validation`, `conversion`, `termine`, `annulation`, `erreur`. Ces phases sont observables par intégration mais ne constituent pas une barre de progression réelle des convertisseurs tiers. Annulation coopérative avant publication atomique ; l’opération tierce en cours ne peut pas être interrompue instantanément. En cas d’erreur, la destination préexistante est conservée.

Sous Windows : `BUILD-WINDOWS-INSTALLER.cmd` pour installateur et portable ; `BUILD-WINDOWS-EXE.cmd` pour EXE uniquement. Les scripts requièrent winget si les outils de compilation manquent.
