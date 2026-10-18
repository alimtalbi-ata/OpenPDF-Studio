# OpenPDF Studio V23.0 — consolidation de qualification

Auteur : Abdelhalim Talbi.

## Livrable
Cette archive cumulative est un **add-on de diagnostic** et non une application Windows native complète. Elle conserve les comparaisons, filtres et exports de V22.9.

## Audit statique de l’interface
Générer un rapport HTML avec `diagnostic_dashboard.py` (voir `--help`), puis lancer `python ui_audit.py chemin/rapport.html --output audit.json`. L’audit vérifie : présence de langue/titre, identifiants dupliqués, labels manquants, liens d’ancrage cassés. Il ne remplace pas les tests clavier, lecteurs d’écran, navigateur ou Windows.

## Tests
`python -m unittest discover -p 'test*.py' -q`; suites JavaScript `node test*.js` individuellement.

## Captures
Voir `CAPTURES-STATUS.md`. Aucune capture Windows native ou validation navigateur réelle revendiquée.
