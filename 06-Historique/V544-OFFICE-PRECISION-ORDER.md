# Historique V544 — Office précision et ordre d’extraction

- **Auteur :** Abdelhalim Talbi.
- **Base :** V543, commit `0edaadf3ba6a300432f1919a0684de31282732b0`.
- **Modification :** seuils optionnels de précision globale, précision par document et rappel ordonné de séquence.
- **Compatibilité :** les manifestes historiques à quatre seuils conservent le schéma de rapport V1 ; l’extension complète produit un rapport V2.
- **Sécurité :** liste blanche du reçu, contrôles d’intégrité hérités V542 et budgets de tokens.
- **Qualification :** workflow V544 ajouté pour Ubuntu/Windows et GUI Linux Xvfb. Les résultats CI doivent être lus depuis GitHub Actions avant de déclarer une campagne verte.
- **Limites :** l’ordre mesuré est l’ordre d’extraction des objets OOXML, pas l’ordre de lecture visuel. Corpus métier indépendant et qualification graphique humaine Windows à réaliser.

- **Correctif V544.1 :** remplacement du balayage glouton non exact par une LCS bit-parallèle ; cas `A B C` / `B C A` et oracle exhaustif (930 comparaisons) ajoutés. Aucun changement de contrat de reçu ou de seuils.
