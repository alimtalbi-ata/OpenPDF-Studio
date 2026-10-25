# OpenPDF Studio V45.2 — Recette OCR réelle Windows
Auteur : Abdelhalim Talbi

Le workflow CI Windows installe Tesseract et vérifie la présence du modèle anglais eng.traineddata. Un test de bout en bout construit un PDF rasterisé ne contenant aucun texte sélectionnable, exécute le vrai moteur OCR PyMuPDF/Tesseract (sans mock) et vérifie que les mots OPENPDF et SCAN deviennent recherchables dans le PDF produit. Le PDF source demeure inchangé.

La qualification ne sera déclarée réussie qu'après validation de GitHub Actions. Cette version ne prouve pas que les modèles Tesseract sont embarqués dans le ZIP Windows ; la livraison autonome des modèles français et anglais reste à traiter. La reconnaissance des scans réels bruités doit encore être qualifiée.
