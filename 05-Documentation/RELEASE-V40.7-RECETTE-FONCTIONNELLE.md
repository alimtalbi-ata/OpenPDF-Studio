# OpenPDF Studio V40.7 — Recette fonctionnelle avec de vrais PDF
Auteur : Abdelhalim Talbi

## Périmètre
Cette version crée des PDF temporaires réels via PyMuPDF, exécute le moteur applicatif (sans mock du moteur PDF), puis réouvre les fichiers générés pour vérifier les résultats.

## Scénarios de qualification
1. Fusion de deux PDF : cinq pages et ordre textuel attendu.
2. Extraction des pages 2 à 3 : contenu et pagination attendus.
3. Réorganisation 3,1,3 : ordre et répétition d'une page.
4. Plage invalide : exception et absence de fichier publié.
5. Collision de destination : fichier existant strictement préservé.
6. Immutabilité des PDF sources : comparaison SHA-256 avant et après.
7. Contrôle des reçus : nombre de pages et SHA-256 du PDF produit.

## Interprétation
Les scénarios sont des tests réels avec PDF générés pendant la CI, pas des captures d'interface Windows. Ils ne couvrent pas la fidélité des conversions Office, l'OCR multilingue, les PDF signés/chiffrés, les fichiers volumineux ni la recette ergonomique manuelle.

## Plan des prochaines versions
V40.8 : corpus de conversion Office et audit des pertes de mise en forme.
V40.9 : journal d'audit structuré, métriques de traitement et erreurs récupérables.
V41.0 : parcours UI guidés, contrôles d'installation sur poste Windows propre, documentation Word/PDF et captures réelles.
