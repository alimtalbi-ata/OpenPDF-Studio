# Historique V556 — vérification stable de l'archive

- Version : V51.4 / jalon sécurité V556.
- Auteur : Abdelhalim Talbi.
- Base : V555 (PR #61), branche dédiée; main non modifiée.
- Problème : le SHA final était calculé par une nouvelle ouverture du chemin après la vérification ZIP. Un remplacement du chemin pouvait rompre le lien entre contenu vérifié et reçu.
- Correction : même descripteur pour le parseur ZIP et les empreintes avant/après; comparaison du fstat et du chemin lstat; refus des entrées non régulières et des changements détectés.
- Régressions ciblées : archive valide, mutation en place de même longueur, remplacement atomique (test POSIX), identité du chemin discordante, dossier au lieu d'un fichier, contrat statique du descripteur partagé.
- Qualification : à confirmer via CI exact-SHA. Aucun build Windows, ZIP, test ou reçu ne doit être inventé ou déclaré réussi avant ses preuves.
- Risque restant : ce contrôle ne remplace pas un verrou de fichier et ne peut empêcher un acteur privilégié d'écrire après le dernier contrôle; SHA-256 n'est pas une signature d'éditeur.
- Suite : consolider la publication cumulative; ensuite mesurer la fidélité PDF vers Office sur un corpus métier indépendant.
