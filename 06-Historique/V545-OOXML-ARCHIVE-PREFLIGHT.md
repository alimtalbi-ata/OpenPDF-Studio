# Historique V545 — prévalidation OOXML

- **Auteur :** Abdelhalim Talbi.
- **Base :** branche V544.1 / commit `f15cec028ebd8ad3c19ecf1261005b38553dff03`.
- **Code :** vérification CRC de chaque entrée ZIP ; rejet des collisions de chemins après normalisation Unicode/casse et des noms ambigus sous Windows.
- **Sécurité :** diagnostics génériques sans nom de membre ; budgets de tailles et ratios conservés ; SHA-256 de fermeture source mis à jour.
- **Tests ajoutés :** paquet valide, collision casefold, point final Windows, périphérique réservé, corruption d'un membre inutilisé.
- **Qualification attendue :** CI ciblée Ubuntu/Windows et tests V542 de régression. Les résultats finaux doivent être consultés dans GitHub Actions avant toute déclaration de réussite.
- **Limites :** CRC ≠ authenticité ni antivirus ; aucune revendication de fidélité visuelle Office ; pas de binaire Windows reconstruit ni de revue graphique humaine avant confirmation des artefacts CI.
