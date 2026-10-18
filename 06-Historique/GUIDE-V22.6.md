# OpenPDF Studio V22.6 — Export contextuel et filtres persistants

Auteur : Abdelhalim Talbi

- Les filtres page, catégorie et gravité restent actifs pendant la navigation des pages dans la session courante.
- Les exports JSON et CSV utilisent le même ensemble de lignes filtrées que le centre de diagnostic.
- Le CSV contient la page logique (index + 1), la page source et la page cible issues du rapport d’appariement ; une valeur vide signifie indisponible.
- Le JSON indique `filteredCount` et `exportedCount`, égaux au nombre d’enregistrements exportés.
- Aucun résultat ne prouve la fidélité d’un document : revue humaine requise.
- Pas de conservation de filtres après rechargement ; pas de test Windows natif ni de capture réelle.
