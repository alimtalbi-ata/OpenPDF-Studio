# OpenPDF Studio V45.0 — Tableaux PDF vers Excel
Auteur : Abdelhalim Talbi

Le convertisseur Excel conserve l'onglet historique « Texte PDF » et ajoute un onglet « Tableau N » par tableau géométrique détecté dans le PDF. Chaque cellule détectée devient une cellule Excel indépendante. Les chaînes commençant par des opérateurs de formule sont neutralisées.

Le test de bout en bout construit un vrai tableau PDF vectoriel, convertit via le dispatcher public et vérifie les cellules du XLSX. Limites : détection dépendante de PyMuPDF et de la géométrie du tableau ; les scans exigent un OCR préalable et les tableaux complexes peuvent être mal détectés. La fidélité globale n'est pas garantie.
