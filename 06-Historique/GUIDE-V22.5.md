# OpenPDF Studio V22.5 — Filtres et exports ciblés

Auteur : Abdelhalim Talbi.

## Nouveautés
- Filtres combinables par gravité, page et catégorie dans le centre des anomalies.
- Compteurs calculés sur les résultats réellement visibles.
- Export JSON contenant le contexte complet, les filtres actifs, le nombre de résultats filtrés et les enregistrements filtrés.
- Export CSV UTF-8 avec BOM, séparateur point-virgule et échappement des champs, limité aux anomalies filtrées.
- Réinitialiser un filtre sur « Toutes… » restaure les résultats correspondants.

## Interprétation
Les filtres ne changent pas les résultats du moteur. Une liste vide signifie seulement qu’aucune anomalie enregistrée ne correspond aux filtres actifs, et non que le document est certifié fidèle. Les scores restent indicatifs.

## Limites
Ce paquet est un add-on/prototype autonome et non l’application Windows complète. Les captures d’écran réelles et la qualification visuelle native restent à effectuer.
