# OpenPDF Studio V25.6 — Dossier d’audit autonome
Auteur : Abdelhalim Talbi

## Parcours simplifié (hors ligne)

1. Dans le tableau de diagnostic, exporter le journal d’audit SHA-256 V25.4.
2. Placer les deux PDF originaux à côté de l’export.
3. Créer un dossier ZIP contenant les **octets exacts** des deux PDF, l’audit lié V25.5, un manifeste SHA-256 et un rapport lisible :

```bash
python audit_dossier_v256.py create audit.json source.pdf cible.pdf -o dossier-audit.zip
```

4. Vérifier le dossier sur un autre poste, sans fichiers externes :

```bash
python audit_dossier_v256.py verify dossier-audit.zip --report verification.txt
```

Un résultat `PASS` confirme la cohérence des empreintes et de la chaîne de preuves. Toute modification d’un PDF ou de l’audit entraîne `FAIL`. Les chemins d’archive sont strictement limités à cinq fichiers nommés. Le rapport est rédigé en français et signale les limites.

**Sécurité :** pas de signature cryptographique, pas de preuve d’identité, pas d’horodatage de confiance. Un acteur pouvant reconstruire l’ensemble du ZIP peut recalculer les empreintes. Les PDF contenus dans le ZIP sont potentiellement sensibles : protéger l’accès au dossier. Le module est un outil CLI hors ligne ; il n’ajoute pas de nouvelle interface graphique ni de qualification Windows native.
