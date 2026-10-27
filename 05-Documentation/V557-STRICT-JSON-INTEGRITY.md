# OpenPDF Studio V51.4 / V557 — JSON strict pour les preuves de publication

Auteur : Abdelhalim Talbi  
Branche dédiée : feature/v51.4-strict-json-release-integrity-v557-20261027  
Base empilée : V556, PR #62. 

main reste intacte et aucune fusion automatique n'est exécutée.

## Problème

Le parseur JSON standard de Python conserve silencieusement la dernière valeur d'une clé d'objet répétée et accepte par défaut NaN/Infinity. Des validateurs différents peuvent ainsi interpréter des reçus de publication de manière divergente.

## Correctif

Le parseur strict V557 détecte les clés dupliquées dans tous les objets imbriqués, refuse les constantes non finies et les encodages UTF-8 invalides, tout en conservant la compatibilité avec un BOM UTF-8. Il est utilisé pour l'inventaire du ZIP cumulatif, le manifeste binaire, les reçus de smoke Windows et le reçu installation/désinstallation.

## Tests fonctionnels

- Clés répétées à la racine et dans des objets imbriqués, y compris dans des tableaux.
- NaN, Infinity et -Infinity.
- BOM UTF-8, texte Unicode valide, UTF-8 invalide et JSON tronqué.
- Rejet d'une archive ZIP synthétique dont l'inventaire réel contient une clé répétée.
- Acceptation d'une archive à inventaire cohérent.
- Le workflow CI exécute les tests sur Ubuntu et Windows.

Les fixtures sont synthétiques. Les tests du parseur ne remplacent pas la qualification native Windows ni la validation finale du ZIP cumulatif.

## Limites

Un JSON strict ne signe pas l'émetteur : SHA-256 vérifie l'intégrité par rapport aux octets calculés, pas l'identité de l'éditeur. La qualification finale reste liée au SHA exact, aux builds Windows, à l'installation/désinstallation et au reçu CRC/inventaire/SHA-256 du ZIP.

## Prochaine priorité

Après consolidation V554–V557, poursuivre l'évaluation indépendante de la conversion PDF vers DOCX/XLSX/PPTX : précision, rappel, ordre des objets, géométrie et fidélité visuelle mesurés séparément.
