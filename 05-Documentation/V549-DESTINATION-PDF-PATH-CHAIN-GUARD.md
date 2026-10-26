# OpenPDF Studio V51.4 / V549 — Garde de la chaîne de destination

**Auteur : Abdelhalim Talbi**  
**Qualification finale : en attente des résultats CI du commit exact.**

## Risque traité

V548 protège les chemins source, mais le contrôle de destination était plus faible : plusieurs opérations normalisaient la sortie avec Path.resolve() après avoir vérifié uniquement le nom final. Un lien ou une jonction dans un répertoire parent pouvait rediriger la publication. Les chemins de découpage et de récupération demandaient également une protection cohérente.

## Modification

- Nouveau module partagé : openpdf_destination_path_guard_v549.py.
- Parcours de chaque composant lexical de la destination avant normalisation, y compris les segments précédant un ...
- Refus des liens symboliques et jonctions Windows dans les chemins parent et final.
- Intégration au dispatcher compression/fusion/extraction/découpage/réorganisation et aux conversions DOCX/XLSX/PPTX.
- Intégration aux points d'entrée directs merge/extract/reorder/split et au chemin de récupération de découpage.
- Les destinations déjà existantes restent protégées ; aucun écrasement n'est introduit.
- Manifeste runtime et pins SHA-256 réconciliés, suite de tests fonctionnels dédiée, guide Word/PDF V549 dépendant des reçus réels.

## Qualification attendue

La CI doit exécuter les tests ciblés sur Ubuntu et Windows. La construction portable et l'installation Windows sont des qualifications natives distinctes. Aucun résultat n'est déclaré réussi avant qu'il soit lié au SHA exact du commit de PR. Les rapports V549 doivent refuser la réutilisation d'une exécution verte d'une autre révision.

## Limites

Il s'agit d'un précontrôle lexical. Il ne supprime pas une course TOCTOU si un autre processus remplace un parent après le contrôle. Les hard links ne sont pas distingués ; aucune détection de malware, signature Authenticode ni revue graphique humaine Windows n'est revendiquée. La fidélité visuelle des conversions Office n'est pas certifiée par ce correctif.

## Prochaine priorité

Réduire la fenêtre TOCTOU par un mécanisme de publication utilisant des descripteurs ouverts lorsque c'est possible, puis poursuivre la qualification de fidélité Office sur un corpus métier annoté indépendamment.
