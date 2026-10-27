# Historique V557 — JSON strict des preuves de livraison

- Version applicative : 51.4 ; jalon sécurité : V557.
- Auteur : Abdelhalim Talbi.
- Base : branche V556 / PR #62 ; branche dédiée V557 ; aucune modification de main.
- Défaut traité : les clés JSON répétées et les constantes numériques non standard pouvaient être acceptées silencieusement par le parseur standard.
- Correction : parseur commun avec détection des clés répétées à tous les niveaux, rejet NaN/Infinity, décodage UTF-8 contrôlé et messages fail-closed. Appliqué à l'inventaire cumulatif, au manifeste binaire et aux reçus Windows.
- Tests ajoutés : JSON valide et BOM, duplications racine/imbrication/tableau, constantes non finies, données invalides et archive ZIP contenant un inventaire ambigu.
- Qualification : attendre les workflows liés au SHA exact de la PR. Aucun binaire, capture d'écran ou reçu de livraison n'est inventé.
- Risques restants : l'intégrité SHA-256 n'authentifie pas l'éditeur ; aucun test de GUI humaine Windows, signature Authenticode, corpus métier OCR ou fidélité Office certifiée n'est revendiqué.
- Suite : consolider la publication cumulative et mesurer la fidélité PDF vers Office sur un corpus métier indépendant.
