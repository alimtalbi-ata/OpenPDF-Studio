# R34 — Repérage visuel des zones d’anomalie

Auteur : Abdelhalim Talbi

`diagnostic_dashboard.py` accepte désormais une liste facultative `page_annotations` dans le rapport JSON. Chaque entrée contient `side` (`source` ou `target`), `page` (numéro à partir de 1), `bbox` (`[x0,y0,x1,y1]` en **points PDF**), `summary` et `severity`.

Exemple : `{"page_annotations":[{"side":"source","page":1,"bbox":[40,40,180,75],"summary":"Bloc à vérifier","severity":"high"}]}`.

Commande : `python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf original.pdf --target-pdf converti.pdf`.

Les rectangles rouges sont tracés uniquement pour les coordonnées explicites valides et contenues dans la page PDF. Aucun emplacement n’est inventé pour les alertes textuelles. Le rendu utilise PyMuPDF et Pillow. Les aperçus sont limités à 24 pages par document et 40 rectangles par page. Les zones ne sont pas encore automatiquement reliées aux anomalies produites par tous les extracteurs.

Aucun essai natif Windows ni capture réelle de l’application n’a été effectué.
