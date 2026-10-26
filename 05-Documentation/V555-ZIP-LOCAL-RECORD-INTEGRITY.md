# OpenPDF Studio V51.4 / V555 — intégrité des enregistrements ZIP

**Auteur : Abdelhalim Talbi**  
**Branche :** \`feature/v51.4-zip-local-record-integrity-v555-20261026\`  
**Base empilée :** V554, PR #60. \`main\` reste inchangée; aucune fusion automatique.

## Priorité et modification

V555 ajoute un précontrôle structurel au vérificateur de ZIP cumulatif. Avant toute lecture du manifeste ou d'un contenu, il rapproche les en-têtes locaux du répertoire central : nom, flags, méthode, CRC, tailles compressées/décompressées. Il vérifie les champs extra de nom Unicode et ZIP64, les descripteurs de données, les offsets et le chevauchement physique des enregistrements.

Les fichiers chiffrés ou utilisant des flags d'en-tête masqué sont refusés. Ce garde-fou complète, sans les remplacer, la politique de ratio V554, les limites absolues, la validation des chemins normalisés et les contrôles SHA-256.

## Tests et niveaux de preuve

Les tests créent des archives déterministes et malformées pour vérifier le comportement avant lecture des membres. Le workflow source-closure exécute la suite sur Ubuntu et Windows et ne démarre le packaging qu'après les tests unitaires.

Une réussite des tests fonctionnels n'est pas une qualification de binaire. La livraison V555 dépend encore de la réussite du build Windows portable, du build d'installateur, des autocontrôles natifs, de l'installation/lancement/désinstallation, puis de la génération du ZIP cumulatif et de la vérification CRC, inventaire et SHA-256 liés au SHA exact.

## Limites

Les archives synthétiques ne sont pas des preuves de livraison. Le contrôle ne garantit pas l'absence de toute vulnérabilité ZIP et ne certifie pas le comportement de chaque extracteur tiers. SHA-256 seul n'authentifie pas l'éditeur; aucune signature Authenticode, revue graphique humaine Windows, exactitude OCR métier ou fidélité Office certifiée n'est revendiquée.

## Prochaine priorité

D'abord résoudre les résultats CI V555 sur le SHA exact et ne publier aucun ZIP tant que la vérification cumulative n'est pas réussie. Ensuite, mesurer la fidélité PDF vers DOCX/XLSX/PPTX sur un corpus métier annoté indépendamment, avec un rapport par document et par page.
