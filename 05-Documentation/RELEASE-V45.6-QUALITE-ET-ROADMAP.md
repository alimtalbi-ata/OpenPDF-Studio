# OpenPDF Studio V45.6 — OCR testé dans les binaires
Auteur : Abdelhalim Talbi

Ajout de `--ocr-self-test` à l'exécutable Windows. Le test vérifie la présence de `fra.traineddata` et `eng.traineddata` dans les ressources embarquées, fabrique un vrai PDF scanné et appelle le moteur OCR réel avec le dossier embarqué explicitement sélectionné. Les tests automatiques Windows exécutent cette vérification dans les deux variantes (installable et portable) et bloquent la publication en cas d'échec.

Cette qualification ne remplace pas un test utilisateur manuel de l'interface graphique sur un poste Windows vierge. La présence éventuelle du moteur Tesseract dans le système de CI reste une limite à tester séparément.
