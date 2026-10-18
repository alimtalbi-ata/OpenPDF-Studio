# OpenPDF Studio V19.9 — Add-on cumulatif de diagnostic
Auteur : Abdelhalim Talbi

## Évolution
Le rapport HTML affiche désormais séparément les candidats de division de page 1→2 et de fusion 2→1 issus de `multipage_audit.split_merge_candidates`, avec les aperçus réels PDF lorsqu’ils sont disponibles. Ces correspondances sont heuristiques et ne constituent pas une preuve de fidélité. Les appariements 1:1 restent inchangés.

## Utilisation
`python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf source.pdf --target-pdf cible.pdf`

## Limites
LibreOffice peut rendre différemment de Microsoft Office. Maximum de 24 aperçus par côté. Aucun test Windows natif ni capture réelle de l’interface. Archive du module de diagnostic uniquement, pas de l’application complète.
