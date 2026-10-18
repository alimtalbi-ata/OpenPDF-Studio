# R32 — Tableau de bord des diagnostics

Auteur : Abdelhalim Talbi.

1. Générer le JSON avec `document_extract.compare_documents()` puis `json.dump(result, file)`.
2. Exécuter `python diagnostic_dashboard.py diagnostic.json diagnostic.html`.
3. Ouvrir `diagnostic.html` localement dans Edge ou Chrome.
4. Filtrer par gravité, exporter les lignes visibles en CSV.

L'export est autonome et fonctionne sans réseau. Les champs dynamiques sont échappés en HTML. Le diagnostic normalise les avertissements, certains écarts de pagination et de tableaux, ainsi que les entrées du centre de diagnostic. Il ne prétend pas couvrir toutes les clés de tous les modules et n'est pas une validation automatique de la qualité de conversion.

**Limites :** l'interface R32 est un rapport HTML distinct, non une intégration à l'interface principale Windows. Aucune capture réelle Windows ni recette Windows native. Les données CSV peuvent contenir des informations confidentielles des documents comparés.
