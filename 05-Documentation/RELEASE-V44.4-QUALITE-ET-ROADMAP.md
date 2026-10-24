# OpenPDF Studio V44.4 — Protection des conversions Office
Auteur : Abdelhalim Talbi

## Correction
Les conversions PDF vers DOCX, XLSX et PPTX vérifient désormais que le PDF source n'a pas changé pendant la conversion, avant toute publication du fichier final. L'identité de la source (taille, horodatage nanoseconde et identifiant de fichier) est capturée avant le convertisseur et revérifiée après l'audit de sortie.

Si la source change, la conversion est rejetée et le fichier temporaire nettoyé. La destination n'est pas publiée.

## Tests
- Mutation du PDF pendant la conversion DOCX simulée : rejet et absence de sortie.
- Source stable : publication et reçu corrects.
- Tests inclus dans GitHub Actions Windows.

## Limites
Les tests injectent un convertisseur simulé et ne prouvent pas la fidélité visuelle/éditabilité des conversions réelles. Une modification extérieure après la dernière vérification reste une fenêtre de concurrence résiduelle.
