# OpenPDF Studio V41.6 — Export d'audit vérifiable
Auteur : Abdelhalim Talbi

## Nouvelles fonctions
- Export JSON structuré depuis le journal local opt-in.
- Empreinte SHA-256 calculée sur la représentation canonique des événements.
- Vérification indépendante de l'export ; détection de modification après export.
- Refus d'écraser un export existant ; rejet des champs non autorisés, notamment les chemins.
- Trois tests automatiques : intégrité, non-écrasement, protection des champs sensibles.

## Limitations et sécurité
L'empreinte SHA-256 n'est pas une signature et n'authentifie pas l'origine du journal. Une personne capable de modifier l'export et de recalculer son empreinte peut fabriquer un export cohérent. Pour une preuve forte, une signature ou un stockage append-only externe sera nécessaire. Export actuellement disponible via API Python, pas encore via l'interface.
