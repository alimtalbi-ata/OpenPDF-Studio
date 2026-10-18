# Qualification native Windows V40.2

1. Placer le contenu de l’archive à la racine du dépôt GitHub (répertoire `02-Compilation` directement sous la racine).
2. Lancer le workflow `.github/workflows/windows-release.yml` avec Actions > Windows release qualification > Run workflow, ou pousser un tag.
3. Attendre la fin du job `build-windows` et récupérer l’artefact `OpenPDF-Studio-V40.2-Windows-binary`.
4. Récupérer les journaux même en cas d’échec via `OpenPDF-Studio-V40.2-build-evidence`.
5. Vérifier que `01-Application/binary` contient les deux `.exe` et leurs rapports liés par SHA-256.
6. Exécuter une recette manuelle UI : ouverture, fusion, découpage, compression, OCR (si Tesseract installé), fermeture, désinstallation.

**Aucun exécutable Windows n’est précompilé dans cette archive.** Un succès des tests Linux ne prouve pas la réussite du workflow Windows.
