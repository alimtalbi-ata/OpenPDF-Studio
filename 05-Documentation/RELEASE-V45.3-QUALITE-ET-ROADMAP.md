# OpenPDF Studio V45.3 — Données OCR embarquées
Auteur : Abdelhalim Talbi

Le script de compilation Windows recherche les modèles de langue OCR locaux dans les dossiers Tesseract-OCR 64 bits ou 32 bits. Lorsqu'un modèle anglais est présent, le dossier tessdata est ajouté aux deux builds PyInstaller (installateur et portable). Le moteur OCR sait déjà retrouver ce dossier depuis sys._MEIPASS.

Le build n'installe pas automatiquement les modèles linguistiques et ne télécharge aucune donnée. Les modèles effectivement inclus dépendent du poste de compilation. Le workflow CI installe Tesseract et vérifie eng.traineddata ; la qualification de la langue française et du comportement sur un poste vierge reste à faire.

Attention : l'application utilise par défaut fra+eng ; si seul eng est fourni, l'utilisateur doit sélectionner eng. Une livraison complètement autonome en français et anglais exige l'inclusion et la qualification des deux modèles.
