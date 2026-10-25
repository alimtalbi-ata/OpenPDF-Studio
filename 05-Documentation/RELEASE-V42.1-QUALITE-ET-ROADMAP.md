# OpenPDF Studio V42.1 — Protection précoce des destinations de compression
Auteur : Abdelhalim Talbi

## Analyse du cas d'usage
Un utilisateur qui demande la compression d'un PDF vers un chemin déjà occupé doit recevoir une erreur claire avant l'exécution coûteuse du moteur, y compris en mode « conserver uniquement si plus petit ». La publication exclusive introduite en V41.9 protège déjà contre la concurrence en fin de traitement, mais ne remplace pas cette validation précoce.

## Développement
- Rejet explicite des destinations existantes ou liens symboliques avant l'ouverture du moteur.
- Préservation du document utilisateur, sans écrasement ni staging inutile.
- Maintien de la publication exclusive finale contre les créations concurrentes.
- Trois nouveaux tests de non-régression sur les profils standard, smaller_only et images_balanced.

## Matrice de qualification
Fonctions P1 : fusion, extraction, découpage, réorganisation et compression. Le présent incrément traite spécifiquement la sécurité de destination de compression. Les contrôles CI ne garantissent ni la qualité visuelle des images compressées ni une recette interactive de l'UI Windows. Aucune capture fictive n'est utilisée.
