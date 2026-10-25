# OpenPDF Studio V45.1 — Refus des faux succès OCR
Auteur : Abdelhalim Talbi

Le moteur OCR vérifie désormais que chaque page raster reconnue produit effectivement du texte exploitable et exactement une page PDF. Si le moteur retourne un PDF vide de texte, l'opération échoue avec un diagnostic français et aucune destination n'est publiée. Le PDF original reste inchangé.

Test de non-régression : une page PDF sans texte reçoit une réponse OCR synthétique sans texte ; le test vérifie le refus de publication et le nettoyage du fichier temporaire.

Limite : ce test valide la sécurité de sortie, pas la qualité de reconnaissance réelle par Tesseract. Une recette OCR réelle avec langues installées et vérification du texte reste obligatoire.
