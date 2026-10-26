# OpenPDF Studio V51.4 — V554 : limitation de l'amplification ZIP

**Auteur : Abdelhalim Talbi**  
**Branche :** `feature/v51.4-archive-expansion-ratio-guard-v554-20261026`  
**Base :** V553 / PR #59. `main` est préservée ; aucune fusion automatique.

## Risque traité

Le vérificateur cumulatif limitait déjà le nombre d'entrées et la taille décompressée totale/par membre. Il pouvait toutefois commencer à décompresser un ZIP dont le ratio de compression était disproportionné. Une archive volontairement compressée peut ainsi consommer beaucoup de CPU, d'E/S et de mémoire avant d'atteindre les limites absolues.

## Modification

- Précontrôle des tailles compressées et décompressées lues dans le répertoire central ZIP avant tout `archive.read()` ou `archive.open()` de contenu.
- Refus d'un membre de **1 MiB ou plus** si son ratio dépasse **200:1**.
- Refus d'une archive dont le contenu décompressé total atteint 1 MiB si son ratio agrégé dépasse **100:1**.
- Conservation des plafonds existants : 200 000 membres, 8 GiB cumulés et 4 GiB par membre.
- Refus de métadonnées de taille négatives ou de types inattendus.
- Tests fonctionnels de bombes à membre unique, d'amplification agrégée par petits membres, d'un ratio borné et de métadonnées invalides.
- Le workflow de fermeture des sources exécute les tests V554 sur Ubuntu et Windows.

## Interprétation des preuves

Les ZIP adversariaux créés par les tests sont des fixtures synthétiques de régression, pas des artefacts de livraison. La réussite du code CI doit être constatée sur le SHA exact de la PR. La qualification des tests Python, le build natif Windows portable, l'installation/désinstallation et la reconstruction du ZIP cumulatif sont des niveaux distincts. Aucun résultat futur n'est présenté ici comme déjà réussi.

## Limites

Les ratios sont une politique conservatrice de sécurité pour les archives de livraison multiplateformes. Ils ne prouvent pas l'absence de toutes les vulnérabilités ZIP, n'authentifient pas l'éditeur et ne remplacent ni le contrôle SHA-256, ni une signature Authenticode. La précision OCR/Office et la revue graphique humaine Windows ne sont pas évaluées par ce changement.

## Prochaine priorité

Après la qualification exacte-SHA de V554, poursuivre la publication résistante aux courses sous Windows, puis qualifier les conversions éditables sur un corpus métier indépendant avec résultats par document et page.
