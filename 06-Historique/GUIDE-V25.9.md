# OpenPDF Studio V25.9 — Assistant d’audit réactif
Auteur : Abdelhalim Talbi

Lancer `LANCER-OPENPDF-AUDIT.cmd` sous Windows (Python 3.9+ et Tkinter nécessaires). Les onglets permettent de constituer ou de vérifier un dossier ZIP de preuves PDF. Un indicateur d’activité apparaît pendant le traitement ; les deux boutons sont désactivés pour éviter des opérations concurrentes. Le rapport indique explicitement SUCCÈS ou ÉCHEC. Le traitement des empreintes et des ZIP s’exécute dans un thread dédié pour préserver la réactivité de la fenêtre. La barre indique une activité, **pas** un pourcentage de progression.

Le bouton de fermeture demande confirmation pendant une opération. Les fichiers ZIP contiennent les PDF originaux : les protéger. Les SHA-256 détectent les modifications mais n’authentifient pas l’auteur. Cette version reste un module de diagnostic, pas un éditeur PDF complet.

## Qualification
Tests automatisés Python/JavaScript sur Linux. Exécution GUI native Windows non réalisée ; aucune capture Windows revendiquée. Captures historiques incluses ; voir CAPTURES-STATUS.md.
