# OpenPDF Studio V45.5 — OCR bilingue réel
Auteur : Abdelhalim Talbi

Le workflow Windows installe Tesseract et ses modèles anglais et français. Si le modèle français est absent, le CI télécharge le modèle officiel `tessdata_fast` de Tesseract depuis GitHub. Le build CI refuse désormais les modèles manquants pour les deux langues. Le test de bout en bout crée une image de texte, génère un PDF sans texte sélectionnable, lance le moteur réel en `fra+eng` et vérifie la présence des mots DOCUMENT et FACTURE dans la sortie.

Qualification en attente de GitHub Actions. Les exécutables restent à tester sur un Windows sans Tesseract installé, avec une vérification du contenu embarqué. La redistribution des modèles doit conserver leurs licences applicables.
