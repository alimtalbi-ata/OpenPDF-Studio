# OpenPDF Studio V20.1 — Guide du centre de diagnostic

Auteur : Abdelhalim Talbi

## Nouveautés

Le rapport HTML autonome propose un champ de recherche textuelle (catégorie, anomalie, page, origine) combinable au filtre de gravité. Le compteur affiche le nombre d’anomalies visibles. L’export CSV n’exporte que les lignes visibles. Les liens vers les pages ouvrent la bonne paire et la font défiler dans la vue. Navigation clavier et focus renforcés.

## Utilisation

`python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf source.pdf --target-pdf cible.pdf`

Ouvrir `rapport.html` dans un navigateur. Saisir une recherche, sélectionner une gravité, cliquer sur une page et naviguer avec Précédent/Suivant.

## Limites

Les comparaisons sont heuristiques. Les aperçus PDF ne sont pas des captures d’interface. L’application Windows complète et sa qualification restent indisponibles.
