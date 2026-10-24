# OpenPDF Studio V51.4 / V526 — ordre de lecture des tableaux en colonnes décalées

Auteur : **Abdelhalim Talbi** — 24 octobre 2026.

## Défaut fonctionnel et correction

Lorsqu'une page PDF contient trois tableaux alignés horizontalement mais décalés verticalement, le classement V524 ancre chaque bande sur son premier tableau. Si A chevauche B et B chevauche C, mais A ne chevauche pas suffisamment C, le tableau C peut être envoyé après A malgré sa position à gauche.

V526 rattache un tableau à une bande si son recouvrement vertical est suffisant avec **au moins un membre** de la bande. La hauteur totale de bande reste bornée à deux fois celle du tableau le plus haut, pour éviter de fusionner artificiellement des rangées distinctes.

## Qualification et reproductibilité

- Test fonctionnel PDF réel **synthétique** : trois tableaux bordés de 4 lignes × 3 colonnes, décalés ; extraction attendue C, B, A ; conversion PDF→XLSX ; 36 cellules ; mutation d'une cellule rejetée.
- Tests unitaires : rangées séparées, chaîne diagonale bornée, géométrie invalide refusée.
- Régressions Excel locales Linux : **113/113 PASS** sur l'archive de sources V525 complétée par V526 (Python 3.13). Tests CI Ubuntu/Windows à consulter séparément sur le commit de PR.
- Il ne s'agit ni d'un corpus métier annoté par des humains, ni d'une mesure de fidélité visuelle.
- La qualification Windows GUI humaine et la signature Authenticode restent absentes.

## Portée et limites

Seul le regroupement géométrique de l'ordre des tableaux est modifié. Aucun changement de version applicative (51.4), de format XLSX, de protection des formules ou du processus de construction Windows.

La lecture multi-colonnes reste heuristique. Prochaine priorité : corpus métier indépendant avec validation manuelle et métriques de précision/rappel, puis corrections guidées par les erreurs observées.

La PR est empilée sur V525. **Ne pas fusionner automatiquement ; préserver main.**
