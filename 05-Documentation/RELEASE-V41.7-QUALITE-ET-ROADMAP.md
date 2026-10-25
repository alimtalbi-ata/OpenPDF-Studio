# OpenPDF Studio V41.7 — Audit depuis l'interface Windows
Auteur : Abdelhalim Talbi

## Interface
- Nouveau bouton Audit dans la barre d'action.
- Fenêtre de confidentialité : activation/désactivation pour la session courante.
- Export du journal JSON avec empreinte SHA-256.
- Vérification d'un export existant, avec retour explicite sur la cohérence.
- Aucune donnée documentaire personnelle ajoutée au journal.

## Limites
L'activation n'est pas persistante entre les sessions. Les captures réelles de l'interface Windows ne sont pas disponibles dans ce commit ; les tests automatisés vérifient la présence des contrôles, pas leur ergonomie visuelle. Le SHA-256 ne constitue pas une signature.
