# Historique V555 — garde d'intégrité structurelle ZIP

- **Auteur :** Abdelhalim Talbi.
- **Parent :** PR #60 / V554, branche \`feature/v51.4-archive-expansion-ratio-guard-v554-20261026\`.
- **Code :** ajout du module de contrôle des en-têtes locaux et des spans, appelé depuis le vérificateur cumulatif avant lecture du manifeste.
- **Sécurité :** validation des noms, flags, méthode, CRC/tailles, champs Unicode/ZIP64, descripteurs, limites d'offset, absence de chevauchement et rejet des octets non indexés entre enregistrements.
- **Tests :** archives normales, ZIP64, divergences d'en-tête, champs Unicode, CRC, descripteurs, entrées chiffrées et chevauchement construit.
- **CI :** la suite doit passer sur Ubuntu et Windows; le build portable, l'installateur et la validation du ZIP sont des étapes distinctes liées au SHA exact.
- **Livraison :** aucune qualification du ZIP cumulatif V555 n'est revendiquée avant les reçus et le contrôle CRC/inventaire/SHA-256 de l'artefact final.
- **Limites :** pas de signature éditeur, de qualification UI humaine Windows ni d'attestation d'exactitude OCR/fidélité Office.
