# R30 — Reconnaissance prudente des tableaux multipages

- Ajout `table_fragment_audit.py` : continuations candidates avec en-têtes répétés sur pages adjacentes, colonnes cohérentes, provenance des fragments, suppression des en-têtes répétés dans la consolidation.
- Signalement des adjacences ambiguës, sans fusion automatique.
- Intégration dans `compare_pdf_office_tables` sous la clé `pdf_fragment_audit`.
- 9 tests unitaires spécifiques à R30 ; 44 tests Python au total, suites JavaScript historiques réussies.
- Aucun test Windows natif ni capture réelle nouvelle.

Auteur : Abdelhalim Talbi.
