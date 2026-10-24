# OpenPDF Studio V44.8 — Recherche des données OCR
Auteur : Abdelhalim Talbi

Le moteur OCR cherche les modèles linguistiques Tesseract requis dans TESSDATA_PREFIX (dossier ou parent), dans le dossier tessdata de l'application empaquetée et dans les emplacements d'installation Tesseract habituels sous Windows. Une configuration explicite sans tous les modèles demandés est rejetée avant tout traitement.

Tests de découverte des langues eng et fra ajoutés. Aucune donnée OCR n'est téléchargée ou intégrée automatiquement. Une recette OCR réelle sur un PDF scanné Windows et le packaging des modèles restent à effectuer; cette version ne doit pas être présentée comme une résolution complète de l'OCR.
