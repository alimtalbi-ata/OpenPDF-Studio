# OpenPDF Studio V18.8 — Add-on R35
Auteur : Abdelhalim Talbi

## Comparaison visuelle côte à côte
La commande `python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf original.pdf --target-pdf cible.pdf` produit un rapport HTML autonome avec les aperçus PDF réels affichés en deux colonnes. Les boutons Page précédente / Page suivante naviguent entre les numéros de pages ayant un aperçu. Les liens d’anomalie sélectionnent la paire correspondante. Sur écran étroit, les aperçus se superposent verticalement. Les encadrements rouges ne sont affichés que si les coordonnées PDF explicites sont disponibles.

**Attention :** les pages sont rapprochées par numéro, pas par alignement sémantique. Un changement de pagination peut donc conduire à une paire non équivalente. Aucun score de similarité d'image n'est calculé. Les aperçus sont des rendus PDF et non des captures de l'application.

## Dépendances
Python, PyMuPDF, Pillow (si surlignage), Node.js pour le pipeline de diagnostic. Le rapport HTML final fonctionne hors ligne.

## Tests
`python -m unittest discover -p 'test*.py' -q` et `for f in test*.js; do node "$f"; done` depuis le répertoire extrait. Les essais Windows natifs et les captures de l'interface ne sont pas encore réalisés.
