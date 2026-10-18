# OpenPDF Studio V23.6 — Zones de différences géométriques

Auteur : Abdelhalim Talbi

1. Exécuter `audit_layout_tables(source_pdf, target_pdf)` pour comparer les pages appariées sur texte normalisé identique.
2. Placer le résultat dans `report["layout_table_audit_v235"]`, puis générer le tableau de bord avec `build_dashboard(report, source_pdf, target_pdf)`.
3. Les anomalies `layout_region` comportent la page, le côté et la zone PDF mesurée ; le rapport affiche les régions lorsque l'aperçu PDF est disponible.
4. Les blocs déplacés affichent une paire de zones source/cible et un extrait de texte pour faciliter la revue humaine.

**Limites :** aucune conclusion de conformité automatique ; pages non appariées exclues, aucun OCR ; les différences de rendu non textuelles peuvent être manquées. L'application Windows native n'est pas qualifiée.
