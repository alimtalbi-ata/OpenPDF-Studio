# OpenPDF Studio V36.9 — Qualification réelle Linux

- 8/8 nouveaux tests V36.9 PASS.
- 19/19 tests V36.7, V36.8 et V36.9 PASS.
- Test os._exit(71) dans un sous-processus puis récupération vérifiée.
- Récupération conservatrice : vérification d’identité de fichier via samefile.
- Journal corrompu / absent : intervention manuelle exigée.
- Pas de test de coupure électrique ni de build natif Windows.
- Garantie multi-fichier atomique : NON.
- fsync de répertoire non effectué sous Windows.
