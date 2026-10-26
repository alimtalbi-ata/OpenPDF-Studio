# OpenPDF Studio V51.4 — V550 : publication PDF ancrée

**Auteur : Abdelhalim Talbi.** Branche dédiée : `feature/v51.4-handle-anchored-publication-v550-20261026`. Cette évolution est empilée sur V549 (#56) ; elle ne modifie pas `main` et ne doit pas être fusionnée automatiquement.

## Modification

Le primitive partagée `openpdf_atomic_output.publish_exclusive` ancre désormais la publication sur des descripteurs de répertoire POSIX ouverts composant par composant, avec refus de suivi des liens. Le fichier temporaire est ouvert sans suivre un lien et son identité est comparée avant publication. Sous Linux lorsque `/proc/self/fd` est disponible, le hard link est créé à partir de l'inode déjà ouvert ; le chemin de staging ne peut donc pas être substitué pour rediriger les octets publiés. Après création, l'inode de sortie est contrôlé, les données et le répertoire sont synchronisés, puis le chemin est rouvert pour vérifier qu'il pointe toujours sur le répertoire épinglé.

Le service de pages PDF réutilise déjà ce primitive pour fusion, extraction et réorganisation ; le dispatcher l'utilise pour les autres sorties transactionnelles passant par le service atomique. Le comportement exclusif sans écrasement et le nettoyage du temporaire restent du ressort du demandeur.

## Tests

La suite V550 contient 11 tests, dont la publication nominale, le refus d'écraser une destination existante, le rejet d'une source temporaire vide, l'échec fermé lorsque le lien dur est indisponible, des chemins symboliques et deux courses adversariales contrôlées (substitution du parent et substitution de l'entrée temporaire). Les tests locaux Linux de cette implémentation ont réussi **11/11 sans skip**. Ce résultat local ne constitue pas la CI du commit GitHub.

La qualification Ubuntu/Windows doit être liée au SHA exact via le rapport `V550-CI-QUALIFICATION.json`. Sous Windows, cinq tests spécifiques aux primitives POSIX/Linux sont attendus en skip et restent explicitement comptabilisés ; cela ne vaut pas qualification du durcissement TOCTOU Windows.

## Limites et risques

- Windows conserve un chemin de publication basé sur les chemins et le garde V549 ; la bibliothèque standard Python ne fournit pas ici d'équivalent portable au parcours POSIX par descripteurs. **La course TOCTOU n'est donc pas déclarée éliminée sous Windows.**
- Sur les systèmes POSIX hors Linux, la publication relative au descripteur utilise le nom relatif sans suivi de lien puis vérifie l'identité de l'inode ; les systèmes de fichiers ou noyaux sans primitives requises refusent la publication.
- Si le parent est déplacé/remplacé pendant la publication, la fonction signale une ambiguïté et laisse l'entrée pour revue manuelle plutôt que de supprimer à l'aveugle un chemin potentiellement remplacé.
- Le mécanisme n'est ni un antivirus ni une certification de fidélité OCR/Office, GUI Windows ou signature Authenticode.

## Livrables de qualification

La CI produit le rapport JSON de qualification V550 et un guide Word/PDF spécifique à ce jalon dans l'archive cumulative Windows. Le diagramme SVG versionné décrit le flux technique ; aucune capture d'écran UI fictive n'est créée.

**Prochaine priorité :** qualifier sous Windows une publication native fondée sur des handles/reparse-point-safe via une API adaptée, avec tests de course réels sur un runner Windows, sans revendiquer une protection plus forte que la preuve obtenue.
