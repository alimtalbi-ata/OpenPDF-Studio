# OpenPDF Studio V546 — Compression contrôlée depuis l’espace de travail

**Auteur : Abdelhalim Talbi**  
**Date : 25 octobre 2026**  
**Branche :** `feature/v51.4-controlled-compression-ui-v546-20261025`  
**Base :** V545 / PR #52, commit `724863da384b9e6e98fecfc9250f903dc7828bc3`

## Problème

Le moteur d’optimisation contrôlée et les profils adaptatifs existaient, mais l’espace de travail principal ne proposait que trois identifiants techniques. Le parcours guidé historique demandait un consentement et un aperçu avant les profils avec perte, alors que le formulaire de travail contournait ce garde-fou. Le mode `auto_quality` n’était pas routé par le dispatcher principal.

## Modification V546

- Remplacement des identifiants bruts de profil par des libellés français explicites, tout en conservant les identifiants stables côté moteur.
- Exposition du profil **Images adaptatif** et du profil **Automatique contrôlé** dans le formulaire principal.
- Consentement explicite et aperçu du PDF source avant tout essai de compression potentiellement avec perte. Le refus du consentement ou de l’aperçu arrête le parcours avant la publication.
- Routage du profil automatique vers le sélecteur qualité existant : essais `smaller_only`, `images_balanced` et `images_adaptive`; seul le candidat conforme le plus petit peut être publié. La publication demeure exclusive, la source reste inchangée et les pertes de structure sont rejetées par la qualification V538.
- Résultat GUI explicite avec tailles avant/après en octets, gain mesuré, profil retenu, pages/pixels comparés, MAE, fraction de pixels modifiés et compteurs structurels utiles.
- Si aucun candidat conforme n’existe, aucun fichier final n’est publié et le journal d’opération consigne `no_output`, pas un succès.

## Qualification automatisée

Le workflow `.github/workflows/compression-ui-v546.yml` exécute sur Ubuntu et Windows :
- compilation statique des modules modifiés ;
- tests unitaires du mapping des profils et du consentement ;
- test fonctionnel sur un PDF réel de fixture créé pendant le test, passant par le dispatcher de production et le moteur automatique ;
- régressions de compression automatique, structure PDF, couverture RGB et transparence ;
- fermeture statique des dépendances runtime.

Les résultats définitifs sont consultables dans GitHub Actions pour le commit de la PR. Ce document ne transforme pas une exécution locale en qualification Windows native : la construction du portable/installateur et les tests de démarrage/installation doivent être vérifiés dans les campagnes Windows dédiées.

## Limites

- Les comparaisons RGB/alpha sont réalisées à une échelle bornée ; elles ne certifient ni rendu imprimé, ni PDF/A, ni accessibilité, ni exactitude OCR.
- Le profil automatique ne remplace pas une validation humaine sur des documents métier.
- La prévisualisation montre la source, pas un rendu côte à côte de chaque candidat.
- La PR reste empilée sur V545 et n’est pas fusionnée automatiquement dans `main`.

## Suite prioritaire

Étendre le corpus autorisé de compression (documents vectoriels, scans, transparence, liens, signets, formulaires et pièces jointes), comparer temps CPU/mémoire et qualité, puis faire une revue interactive humaine de la GUI sous Windows.
