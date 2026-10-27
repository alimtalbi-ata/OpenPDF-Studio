# Historique V558 — bornes JSON et Unicode

- Version applicative : 51.4 ; jalon sécurité : V558.
- Auteur : Abdelhalim Talbi.
- Base : V557 / PR #63 ; branche dédiée ; aucun merge automatique.
- Correctif : plafonds de charge JSON (32 MiB), nesting (128), entiers (signé 64 bits) et validation des scalaires Unicode après parsing.
- Défenses conservées : clés dupliquées refusées à tous niveaux, nombres non finis rejetés, UTF-8 invalide/tronqué refusé, BOM UTF-8 accepté.
- Tests ajoutés : taille et profondeur refusées avant l'appel au parseur, limites int64, substituts isolés dans clé/valeur, caractère supplémentaire valide, inventaire ZIP ambigu et archive cohérente.
- Qualification : tests Ubuntu/Windows, build portable, installateur, installation/désinstallation et ZIP cumulatif doivent tous être verts pour le SHA exact. Aucune preuve n'est simulée.
- Risques résiduels : les bornes ne garantissent pas une sécurité universelle des consommateurs JSON ni l'authenticité des binaires ; aucune signature Authenticode ni certification métier n'est revendiquée.
- Prochaine étape : qualifier indépendamment la conversion PDF vers Office sur des documents annotés.
