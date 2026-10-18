# OpenPDF Studio V21.0 — Régions d’écarts visuels
Auteur : Abdelhalim Talbi

Dans le rapport HTML, activer la superposition, sélectionner une paire de pages, puis cliquer sur **Visualiser les écarts après recalage**. La carte de luminance rouge présente maintenant jusqu’à cinq régions d’écarts entourées en bleu et numérotées. Le regroupement est fait sur une grille de 8 × 8 pixels de la carte 384 × 384. Les groupes de moins de trois cellules sont écartés. Le seuil reste réglable de 10 à 100. Modifier une paire ou un paramètre invalide la carte jusqu’à un nouveau calcul.

Les régions sont des **candidats géométriques** et ne permettent pas de distinguer avec certitude les modifications de texte, les objets déplacés, les effets d’anticrénelage et les variations de police. Le recalage n’est pas une preuve de fidélité.

Tests : `python -m unittest discover -p 'test*.py'` et `node test_regions_v210.js`. Cette archive est un add-on, pas l’application Windows complète.
