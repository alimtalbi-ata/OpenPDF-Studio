# Historique V554 — limitation de l'amplification ZIP

- **Auteur :** Abdelhalim Talbi.
- **Base :** V553 / PR #59, branche `feature/v51.4-archive-nfkc-collision-guard-v553-20261026`.
- **Code :** `package_cumulative_v434.py` précontrôle les ratios de décompression à partir du répertoire central ZIP avant de lire les contenus.
- **Limites :** ratio membre 200:1 (membres d'au moins 1 MiB), ratio archive 100:1 (contenu total d'au moins 1 MiB), en plus des plafonds existants 200 000 membres / 8 GiB cumulés / 4 GiB par membre.
- **Tests :** ajout de `test_package_expansion_ratio_v554.py` couvrant bombe à membre unique, amplification agrégée de petits membres, fixture à ratio raisonnable et métadonnées invalides.
- **CI :** nouveau test relié au workflow de qualification sources sur Ubuntu et Windows. Les résultats ne sont recevables qu'à partir du SHA exact de PR.
- **Livraison :** aucun EXE/ZIP cumulatif V554 n'est revendiqué avant la reconstruction par le workflow de packaging et la vérification de ses reçus.
- **Limites :** pas d'authentification éditeur, de signature Authenticode ni d'attestation de revue graphique humaine.
