# OpenPDF Studio V123.0 — diagnostic add-on
Auteur : Abdelhalim Talbi

## Numérotation
Retour à la numérotation produit **V123.0**. Ce livrable reste un add-on cumulatif dérivé de R36 ; il ne constitue pas l’application Windows complète.

## Nouveauté
`multipage_audit.detect_split_merge_candidates` signale les cas possibles d'une page source répartie sur deux pages cibles, ou de deux pages source réunies en une page cible. L'analyse est textuelle et heuristique, fondée sur le recouvrement de mots ; aucune fusion automatique ni équivalence visuelle certifiée. Les résultats sont disponibles sous `multipage_audit.split_merge_candidates`.

## Tests
`python -m unittest discover -p 'test*.py'` puis `node test.js` et les autres scripts `test-r*.js`.

## Limites
L’interface HTML de comparaison côte à côte reste appariée en 1:1 ; les candidats 1:2 et 2:1 sont fournis dans le JSON pour intégration ultérieure. Aucune recette Windows native ni capture réelle de l’application n’a été effectuée.
