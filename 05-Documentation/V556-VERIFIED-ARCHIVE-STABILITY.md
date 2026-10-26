# OpenPDF Studio V51.4 / V556 — stabilité de la vérification de l'archive

Auteur : Abdelhalim Talbi  
Branche dédiée : feature/v51.4-archive-verification-stability-v556-20261026  
Base empilée : V555, PR #61. main est préservée; aucune fusion automatique.

## Priorité et changement produit

La fonction de vérification du ZIP cumulatif validait les entrées et l'inventaire à travers un descripteur, fermait le lecteur ZIP, puis rouvrait le chemin pour calculer le SHA-256 de sortie. Un remplacement du chemin dans cet intervalle pouvait dissocier les données vérifiées de l'empreinte retournée. V556 relie le reçu au même descripteur utilisé pendant toute la lecture : précontrôle lstat, refus des entrées non régulières, identité du fichier ouvert et du chemin, SHA-256 initial/final, contrôle de l'identité à la fin.

Les gardes précédentes demeurent obligatoires : V553 pour les collisions de chemins normalisés, V554 pour les ratios d'expansion, V555 pour la structure locale/centrale et EOCD, et le manifeste/checksum SHA-256 pour chaque membre.

## Tests fonctionnels ajoutés

- Une archive synthétique cohérente est acceptée et retourne l'empreinte exacte des octets vérifiés.
- Une mutation en place à longueur ZIP identique pendant le précontrôle est refusée.
- Un remplacement atomique du chemin pendant la vérification est refusé sur POSIX; un test de contrat identitaire couvre aussi les autres OS.
- Un dossier est refusé comme entrée d'archive.
- Un contrat statique vérifie que parseur ZIP et calcul d'empreinte partagent le même flux ouvert.

Les fixtures sont des tests, non des reçus de livraison. Les tests fonctionnels ne remplacent pas les builds Windows natifs ni le contrôle final d'inventaire/CRC/SHA-256.

## Limites

Le contrôle détecte les modifications observées pendant son cycle; il ne constitue pas un verrou contre un acteur privilégié capable de modifier le fichier après le dernier contrôle. SHA-256 vérifie l'intégrité, pas l'identité de l'éditeur. Aucune signature Authenticode, revue graphique humaine, certification OCR métier ou fidélité Office certifiée n'est revendiquée.

## Qualification exigée

La CI doit réussir sur le SHA exact de la PR empilée : tests Ubuntu/Windows, fermeture statique des sources, portable Windows, installateur, tests natifs, installation/désinstallation silencieuses, packaging cumulatif et vérification CRC, inventaire, reçus binaires et SHA-256. L'archive n'est pas déclarée qualifiée avant la dernière étape.

## Prochaine priorité

Après CI verte, poursuivre la consolidation cumulative et bâtir un corpus métier Office annoté par des réviseurs indépendants, mesurant séparément le rappel, la précision, l'ordre, la géométrie et la fidélité visuelle.
