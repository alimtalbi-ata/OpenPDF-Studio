# OpenPDF Studio V20.3 — Localisation textuelle contrôlée

Auteur : Abdelhalim Talbi

## Fonction
Le rapport peut inclure `text_differences`, liste d’objets `{ "side": "source", "page": 1, "text": "fragment exact" }`. Quand le PDF correspondant est fourni (`--source-pdf` ou `--target-pdf`), PyMuPDF cherche le fragment dans la couche texte native. Un encadrement est produit **uniquement si une occurrence unique** est trouvée. Les textes absents, répétés, hors page ou trop longs restent sans localisation. Il ne s'agit ni d'OCR ni d'une preuve de fidélité de conversion.

## Utilisation
`python diagnostic_dashboard.py --help`

## Limitations
Add-on de diagnostic uniquement, pas d'application Windows native livrée. Aucun test Windows ni capture réelle d’interface effectués dans cet environnement. Les aperçus PDF sont des rendus de documents, pas des captures d’interface.
