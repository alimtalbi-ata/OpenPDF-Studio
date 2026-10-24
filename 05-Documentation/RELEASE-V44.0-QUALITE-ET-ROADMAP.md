# OpenPDF Studio V44.0 — Déduplication des rendus d'aperçu
Auteur : Abdelhalim Talbi

## Correction
La V43.8 a supprimé le blocage des demandes de générations différentes, mais permettait plusieurs rendus concurrents de la même page et de la même génération. La V44.0 déduplique précisément sur le couple (document/page, génération) sans réintroduire le blocage V43.8.

- Une demande identique déjà en cours ne lance plus de thread de rendu supplémentaire.
- Une génération plus récente reste indépendante des rendus obsolètes.
- Une page différente peut être rendue sans attendre l'autre.
- Trois tests de non-régression ajoutés à la CI Windows.

## Limites
Cette correction évite des tâches redondantes; elle ne garantit pas une limite globale du nombre de threads ni une recette graphique Windows interactive.
