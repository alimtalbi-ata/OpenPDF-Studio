# OpenPDF Studio V41.0 — Documentation cumulative traçable
Auteur : Abdelhalim Talbi

## Évolutions
- Génération automatique des guides Word et PDF propres à la version V41.0 pendant la CI Windows, avant la constitution de l'archive cumulative.
- Échec explicite de génération si les notes de version sont absentes.
- Guide : architecture, installation, compilation, utilisation, qualification, limites, fonctionnalités et notes de version.
- Manifestes SHA-256 du ZIP incluant les documents effectivement produits.
- Les documents historiques sont conservés mais ne sont pas confondus avec les guides V41.0.

## Périmètre de preuve
La génération DOCX/PDF est exécutée en CI; aucune capture d'interface réelle n'est fabriquée. La fidélité visuelle des conversions Office et les tests manuels d'ergonomie restent à qualifier.

## Suite
V41.1 : journal d'audit structuré, navigation UI par tâche, qualification de la conversion de tableaux et de la compression sur corpus représentatif.
