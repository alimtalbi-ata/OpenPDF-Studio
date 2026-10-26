# OpenPDF Studio V51.4 — V551 : publication Windows par handles

**Auteur : Abdelhalim Talbi.** Branche dédiée : \`feature/v51.4-windows-handle-publication-v551-20261026\`, empilée sur V550 (#57). \`main\` reste intacte ; aucun merge automatique.

## Priorité

Le primitive de sortie V550 supprime déjà le repli fondé sur les chemins sous POSIX, mais conservait V549 sous Windows. Les opérations PDF (compression, fusion, extraction, découpage et réorganisation) qui publient via le primitive partagé ne disposaient donc pas d'une publication ancrée équivalente sous Windows.

## Modification

- Ajoute \`openpdf_windows_handle_publish_v551.py\`, à base de \`ctypes\`, pour ouvrir le parent composant par composant avec \`NtCreateFile\`, \`OBJ_DONT_REPARSE\` et \`FILE_OPEN_REPARSE_POINT\`.
- Ouvre le temporaire par rapport au handle du parent et conserve ce handle sans partage de suppression pendant la publication.
- Publie avec \`NtSetInformationFile(FileLinkInformation)\`, nom relatif au handle du répertoire et \`ReplaceIfExists = false\` : aucune réécriture d'une destination existante n'est permise.
- Vérifie l'identité volume/fichier du résultat, puis rouvre le chemin et vérifie que le répertoire nommé correspond toujours au handle épinglé.
- Refuse les chemins UNC, lecteurs réseau mappés, segments \`..\`, composants ambigus, reparse points dans la chaîne et environnements ne prenant pas en charge les primitives requises.
- Le dispatcher \`openpdf_atomic_output.publish_exclusive\` envoie le chemin Windows vers ce nouveau backend ; il n'abaisse pas silencieusement la protection vers \`os.link(Path, Path)\`.

## Tests et qualification

La suite V551 vérifie le parcours nominal, l'intégration du dispatcher, le non-écrasement, les jonctions, le segment \`..\`, une substitution de répertoire pendant l'opération et l'impossibilité de renommer le temporaire lorsqu'il est épinglé.

- Ubuntu : seules les deux vérifications indépendantes du système et du dispatch s'exécutent ; les six tests nécessitant l'API Windows sont des ignorés documentés.
- Windows : les huit tests sont requis sans aucun ignoré.
- Le rapport \`04-Tests-et-Qualification/V551-CI-QUALIFICATION.json\` doit être généré à partir des logs GitHub Actions de la même révision et du reçu V550 de même SHA. Des fixtures de tests du parseur ne sont jamais utilisées comme preuve de CI.
- Le guide Word/PDF du jalon est produit par \`02-Compilation/generate_docs_v551.py\` uniquement avec un reçu correspondant au SHA courant pour afficher les résultats comme qualifiés ; un reçu absent ou périmé affiche explicitement NON QUALIFIÉ.

## Limites

Le backend est réservé aux chemins locaux à lettre de lecteur et aux systèmes de fichiers permettant le lien dur exclusif. Les chemins UNC, lecteurs réseau et systèmes de fichiers incompatibles échouent fermé. L'ouverture et la conservation des handles limitent la redirection vers un répertoire substitué après son épinglage ; le code vérifie les changements observables et conserve la sortie pour examen si un déplacement rend l'opération ambiguë.

Cette évolution **ne revendique pas l'élimination absolue de toutes les courses TOCTOU sous Windows**. Les tests CI doivent encore confirmer le comportement effectif sur le runner Windows avant qu'un reçu qualifié soit publié. Ne pas confondre compilation statique ou tests Linux avec cette qualification native.

La PR ne certifie ni fidélité métier OCR/Office, ni revue graphique humaine sous Windows, ni signature Authenticode. Aucune capture d'écran n'est fabriquée ; le SVG fourni est un diagramme d'architecture.

## Livrables

- Backend : \`03-Sources/openpdf_windows_handle_publish_v551.py\`
- Intégration : \`03-Sources/openpdf_atomic_output.py\`
- Tests : \`04-Tests-et-Qualification/test_atomic_output_v551.py\`
- Reconciliation de preuve : \`02-Compilation/write_v551_ci_qualification.py\`
- Guide généré après qualification : \`OpenPDF-Studio-V51.4-V551-Guide.docx\` et \`OpenPDF-Studio-V51.4-V551-Guide.pdf\`
