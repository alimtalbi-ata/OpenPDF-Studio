# Historique V547 — Garde des sources PDF symboliques

**Auteur : Abdelhalim Talbi — 25 octobre 2026**

- Corrige l'ordre de validation des chemins source dans le dispatcher et le service de pages PDF.
- Rejette les chemins sources dont le composant final est un lien symbolique avant leur canonicalisation.
- Ajoute des tests multi-plateformes sur fusion, extraction, réorganisation, découpage et compression, ainsi qu'un essai de lien de fichier réel lorsque les permissions l'autorisent.
- Étend le workflow de régression des opérations de pages et ajoute les empreintes SHA-256 des modules runtime modifiés au manifeste V51.4.
- Assemble un ZIP cumulatif depuis les deux artefacts Windows natifs qualifiés ; régénère le manifeste binaire, le guide Word/PDF, le manifeste SHA-256 et la preuve de vérification avant publication de l'artefact.

**Statut de preuve :** les tests sont déclenchés par la PR V547. Les résultats doivent être constatés dans GitHub Actions. Aucun résultat, capture UI ou binaire n'est présumé avant l'exécution des workflows.

**Risques connus :** les liens symboliques dans les répertoires parents restent permis ; le contrôle ne constitue pas une garantie absolue contre les changements concurrents de chemin.
