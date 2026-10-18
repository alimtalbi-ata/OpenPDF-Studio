# OpenPDF Studio V20.0 — Guide du module de diagnostic

Auteur : Abdelhalim Talbi

## Nouveauté
Le rapport HTML contient une section **Fiabilité du diagnostic** qui distingue la présence des preuves (géométrie, pagination, tableaux, annotations) d’une véritable certification de fidélité. Aucun pourcentage de précision n’est inventé.

## Utilisation
`python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf source.pdf --target-pdf cible.pdf`

Le rendu PDF des documents Office reste optionnel et dépend de LibreOffice. Le module est autonome et ne remplace pas l’application Windows complète.

## Qualification
Exécuter `python -m unittest discover -p 'test*.py'` et `node test.js` puis les autres suites `test*.js`. Les aperçus PDF ne sont pas des captures de l’interface Windows.
