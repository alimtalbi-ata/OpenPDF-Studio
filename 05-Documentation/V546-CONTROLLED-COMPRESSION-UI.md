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

## Addendum V546.1 — Comparaison des candidats

Le résultat de compression affiche maintenant une ligne par profil réellement essayé : disposition (retenu / conforme mais non retenu / aucun gain / rejeté), taille et gain mesurés quand un candidat passe, MAE et fraction de pixels modifiés, ainsi que la durée de l’essai. En l’absence de résultat conforme, les motifs restent compréhensibles sans publier de sortie.

Les détails d’exception bruts, chemins absolus et noms de fichiers internes ne sont pas recopiés dans ces lignes de diagnostic. Cette sortie UI reste un résumé : elle ne remplace ni le reçu technique complet en mémoire du moteur, ni une certification de fidélité métier.

## Addendum V546.1 - Intégrité des reçus de packaging Windows

Le contrôle de packaging cumulatif V43.4 supposait deux contrôles smoke par exécutable. La qualification native V51.4 en produit désormais trois : démarrage, test fonctionnel et test du runtime OCR. Cette divergence bloquait le paquet cumulatif même quand les trois contrôles natifs étaient réussis.

Le validateur validate_smoke_receipt vérifie maintenant exactement les trois arguments attendus, leur unicité, exit_code=0, passed=true, timed_out=false, des sorties texte et la liaison du reçu à la version, au mode, au nom et au SHA-256 de l'exécutable. Les reçus de deux contrôles seulement sont refusés. Dix tests ciblés couvrent le chemin nominal, les omissions, les doublons, l'échec simulé, les délais dépassés et les identités divergentes.

La modification du validateur ne constitue pas un nouveau résultat de test Windows : les tests du contrat de reçu sont exécutés sur Ubuntu et Windows via le workflow V546.1, et le package final doit encore passer son propre contrôle d'intégrité.
