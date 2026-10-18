# OpenPDF Studio V22.4 — Synthèse des anomalies par page

Auteur : Abdelhalim Talbi

## Nouveautés
- Panneau « Synthèse par page » intégré au comparateur.
- Comptage des anomalies du centre de diagnostic pour la page active.
- Récapitulatif des éléments manquants, ajoutés et déplacés et du score indicatif.
- Répartition des anomalies par gravité et catégorie.
- Message explicite lorsque la page n’a aucune anomalie enregistrée.
- Export renommé en `diagnostic-v22.4.json` et `qualification-v22.4.html`.

## Interprétation et limites
Les compteurs proviennent des données structurées déjà calculées par le comparateur. Ils ne constituent pas une certification de fidélité. Une absence d’anomalie enregistrée ne prouve pas que la conversion est parfaite. L’aperçu reste un modèle de blocs textuels et non un rendu natif de PDF/Office.

## Qualification
Lancer les tests avec `python -m pytest -q`. Le test navigateur natif, les captures réelles et la qualification Windows doivent être effectués séparément.
