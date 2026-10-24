# OpenPDF Studio V44.6 — Rotation PDF fonctionnelle
Auteur : Abdelhalim Talbi

La rotation des pages PDF est maintenant proposée dans l'interface : 90, 180 ou 270 degrés. Le moteur PyMuPDF applique une rotation native sans rasteriser les pages et crée un nouveau PDF sans écraser la source. Les tests de bout en bout vérifient les trois angles, le texte conservé et le rejet d'un angle non valide.

Les conversions Office existantes ne préservent pas la mise en page complexe. L'OCR exige Tesseract et ses données de langue; leur disponibilité dans l'installation Windows reste à qualifier. Le succès de la CI n'équivaut pas à une recette manuelle de l'interface graphique.
