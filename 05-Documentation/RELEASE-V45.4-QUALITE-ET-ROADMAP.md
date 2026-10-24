# OpenPDF Studio V45.4 — OCR portable-only sécurisé
Auteur : Abdelhalim Talbi

Le staging des modèles Tesseract intervient désormais avant la bifurcation installer/portable. La compilation `--portable-only` ne peut plus produire un binaire dépourvu de modèles simplement parce que la préparation a été sautée. Le staging est nettoyé avant chaque compilation afin de ne pas réutiliser d'anciens modèles.

En CI, l'absence de `eng.traineddata` bloque explicitement la release. Hors CI, la compilation peut rester optionnelle et dépend de la présence de Tesseract. La prise en charge du français et la vérification OCR sur machine vierge restent à qualifier.
