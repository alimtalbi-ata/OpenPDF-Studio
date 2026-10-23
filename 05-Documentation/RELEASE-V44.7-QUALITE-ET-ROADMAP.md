# OpenPDF Studio V44.7 — Diagnostic OCR Windows
Auteur : Abdelhalim Talbi

Le moteur OCR retourne désormais un message explicite lorsque Tesseract ou les modèles de langue sont absents. Le message précise les langues attendues et TESSDATA_PREFIX. Le fichier PDF de sortie n'est pas publié si l'OCR échoue.

Un test de régression simule uniquement la panne de dépendance et vérifie la non-publication. Ce test ne prouve pas qu'un vrai PDF scanné peut être reconnu dans le binaire Windows. La distribution autonome de Tesseract et des données fra/eng reste à développer et qualifier, de même que la fidélité des conversions Office.
