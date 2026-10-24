# OpenPDF Studio V43.5 — Validation immédiate des paramètres de pages
Auteur : Abdelhalim Talbi

## Expérience utilisateur
Les opérations d'extraction, découpage et réorganisation disposent désormais d'une validation de leurs paramètres avant le lancement du traitement asynchrone. Les erreurs sont affichées dans la boîte de dialogue « Paramètres invalides », sans démarrer de tâche.

- Extraction : bornes entières positives et intervalle ordonné.
- Découpage : nombre entier strictement positif de pages par fichier.
- Réorganisation : liste de numéros de pages non vide, sans élément manquant ou négatif.
- Huit tests unitaires couvrant paramètres valides et invalides.

## Limites
La validation des numéros par rapport au nombre réel de pages reste assurée par les services PDF. Les tests automatisés ne remplacent pas la recette interactive de l'interface Windows.
