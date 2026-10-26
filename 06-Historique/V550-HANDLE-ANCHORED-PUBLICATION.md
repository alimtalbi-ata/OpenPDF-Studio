# Historique V550 — publication ancrée

- **Priorité :** fermer la fenêtre TOCTOU du primitive de publication partagé identifiée dans V549.
- **Implémentation :** marche de répertoires POSIX via descripteurs `O_DIRECTORY | O_NOFOLLOW`, ouverture du temporaire sans suivi de lien, liaison exclusive depuis l'inode ouvert via `/proc/self/fd` sous Linux, contrôle de l'identité après publication et vérification que le chemin pointe toujours sur le répertoire épinglé.
- **Portée produit :** le service partagé sert les opérations atomiques de fusion, extraction, réorganisation et les flux appelant le dispatcher.
- **Tests :** 11/11 réussis localement sous Linux sans skip avant push ; tests Windows natifs et CI du commit final requis.
- **Limite explicite :** Windows utilise le repli par chemins avec précontrôle ; aucune élimination complète de TOCTOU n'est revendiquée. Une sortie ambiguë après déplacement du parent est préservée pour revue, pas supprimée à l'aveugle.
- **Auteur :** Abdelhalim Talbi.
