# Historique V553 — collisions Unicode des chemins d'archive

- **Auteur :** Abdelhalim Talbi.
- **Base :** PR #58, publication Windows par handles V551 ; `main` n'est pas modifiée.
- **Code :** identité de chemin NFKC + casefold dans `package_cumulative_v434.py`, refus des normalisations qui changent le nombre de séparateurs, détection des collisions entre fichiers, répertoires et chemins parents.
- **Tests :** six tests adversariaux ZIP/inventaire, dont deux entrées fichier sous des répertoires parents NFKC-équivalents sans entrées de répertoire explicites ; exécutés par workflow sur Ubuntu et Windows.
- **Preuves :** la CI doit réussir sur le SHA final. Les fixtures de test ne sont pas des reçus de publication.
- **Limites :** la somme SHA-256 vérifie l'intégrité du contenu mais ne fournit pas d'authentification de l'éditeur ; pas de signature Authenticode.
