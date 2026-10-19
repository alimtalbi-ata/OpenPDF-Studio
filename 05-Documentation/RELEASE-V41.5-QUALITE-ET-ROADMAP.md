# OpenPDF Studio V41.5 — Journal d'audit local opt-in
Auteur : Abdelhalim Talbi

## Fonctionnalités
- Audit désactivé par défaut. Activation explicite via OPENPDF_AUDIT=1.
- Dossier configurable via OPENPDF_AUDIT_DIR ; sinon dossier personnel .openpdf-studio.
- Enregistrement JSONL : horodatage UTC, opération, statut succès/échec et durée en millisecondes.
- Aucune collecte des chemins source/destination, noms de fichiers ou contenus PDF.
- Rotation locale vers operations.previous.jsonl dès que le journal dépasse 1 Mio.
- Un échec d'écriture de l'audit n'interrompt jamais une opération PDF.
- Tests : absence de journal par défaut, rotation, champs minimaux, rejet des événements non reconnus.

## Limites
Le journal est local et non signé ; l'intégrité cryptographique et les verrous interprocessus restent à développer. L'activation nécessite une variable d'environnement et n'est pas encore exposée dans l'interface graphique.
