# V39.4 — Qualification

- Correction : le rapport smoke Windows annonçait à tort V39.0.
- Vérification PE renforcée : MZ, offset et signature PE.
- Publication : les deux builds sont validés avant copie finale en mode all. ATTENTION : les copies ne constituent pas une transaction atomique multi-fichiers ; une panne pendant publication peut laisser un jeu mixte.
- Tests natifs Windows non exécutés : environnement Linux.
- Aucun EXE Windows précompilé.
