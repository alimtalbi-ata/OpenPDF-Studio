# OpenPDF Studio V40.8 — Qualification OCR et annulation
Auteur : Abdelhalim Talbi

## Évolutions de qualification
Les tests exécutent réellement le service OCR sur des PDF créés en mémoire, sans simuler le moteur PDF. Ils vérifient :
- Conservation du texte et du nombre de pages en mode « ignorer les pages déjà textuelles ».
- Exactitude des reçus : SHA-256, taille et compteurs de pages.
- Interruption simulée via callback avant publication : aucune sortie et aucun fichier temporaire résiduel.
- Rejet des paramètres de langue non conformes.
- Refus d'écrasement des destinations existantes.
- Rejet d'un répertoire tessdata absent.

## Limites
Ces tests ne démontrent PAS la reconnaissance optique d'une page scannée : ce chemin nécessite une installation Tesseract et des données linguistiques. La CI ne prouve pas non plus l'accessibilité UI ni la fidélité des conversions Office.

## Prochaines étapes
V40.9 : tests de conversion Office avec corpus et score de contenu.
V41.0 : audit JSON de bout en bout, installation Windows propre et documentation Word/PDF actualisée.
