# Guide R27 — Audit des frontières de pages

Auteur : Abdelhalim Talbi

`from boundary_audit import audit_page_boundaries` puis `audit_page_boundaries(pages)` retourne les frontières candidates.

Pour des fichiers réels : `from document_extract import compare_documents` puis `compare_documents("source.pdf", "cible.docx", render_office=True)`.

Lire `result["boundary_audit"]["source"]` et `["target"]`. La conversion Office demande LibreOffice ; les autres dépendances restent celles du projet. Les correspondances ne prouvent pas une fidélité visuelle.
