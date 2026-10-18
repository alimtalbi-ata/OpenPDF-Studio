# OpenPDF Studio V25.4 — Guide utilisateur
Auteur : Abdelhalim Talbi

## Export d'un audit intègre
1. Ouvrir un rapport HTML généré par `diagnostic_dashboard.py`.
2. Afficher les régions vérifiées et sélectionner une ou plusieurs régions source/cible.
3. Cliquer sur **Exporter audit SHA-256 vérifiable**.
4. Conserver le JSON téléchargé et le transmettre au vérificateur :

```bash
python verify_proof_audit_v254.py openpdf-region-audit-sha256-v25.4.json
```

Le code de retour vaut 0 si le contenu et la chaîne sont cohérents, 1 sinon. Chaque entrée contient l'empreinte de l'entrée précédente et ses coordonnées PDF. Les pages non appariées sont conservées avec leur statut, sans affirmer une correspondance entre régions source/cible.

## Limites importantes
- **Intégrité, pas authenticité** : un acteur peut régénérer une chaîne entière ; il n'y a ni signature numérique ni horodatage de confiance.
- La chaîne protège uniquement les entrées exportées ; elle ne prouve pas que le PDF source n'a pas été modifié. Conserver les PDF et leurs empreintes séparément.
- Journal limité à 100 événements en mémoire navigateur ; l'export ne constitue pas une conservation persistante.
- Tests visuels effectués sous Chromium Linux headless, pas sous Windows natif.
- Il s'agit d'un module de diagnostic, non de la suite bureautique complète.
