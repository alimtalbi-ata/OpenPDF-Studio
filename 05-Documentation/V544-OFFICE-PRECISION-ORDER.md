# OpenPDF Studio V544 — précision des mots et ordre d’extraction Office

**Auteur : Abdelhalim Talbi — 25 octobre 2026**

## Priorité et défaut traité

Le gate V542 pouvait réussir lorsqu’une conversion conservait tous les mots de référence mais ajoutait du texte parasite ou réordonnait les mots. Un rappel de 100 % ne mesure ni la précision ni l’ordre.

V544 ajoute une qualification étendue facultative pour Word (DOCX), Excel (XLSX) et PowerPoint (PPTX), tout en conservant les manifestes V542 historiques à quatre seuils. Les décisions utilisent les valeurs non arrondies.

## Seuils étendus

Les quatre seuils V542 restent obligatoires :

- `min_token_recall`
- `min_case_token_recall`
- `min_human_reviewed`
- `min_editable_elements_per_case`

Pour activer V544, ajouter **les trois** seuils suivants. Ils doivent être présents ensemble :

- `min_token_precision` : correspondances / mots réellement extraits sur tout le corpus.
- `min_case_token_precision` : précision minimale exigée dans chaque document.
- `min_case_ordered_token_recall` : rappel minimal en ordre dans chaque document.

Exemple de valeurs strictes pour un corpus contrôlé : `0.98`, `0.95`, `0.90`. Elles sont des exemples de politique, pas des seuils universels adaptés à chaque métier.

## Métriques

Pour chaque document, V544 compare les tokens normalisés Unicode NFKC et casse neutralisée. Les occurrences répétées ne comptent qu’à concurrence de la référence.

- **Précision** = tokens attendus correctement retrouvés / total des tokens extraits.
- **Rappel** = tokens attendus correctement retrouvés / total des tokens de référence.
- **F1** = moyenne harmonique de la précision et du rappel.
- **Rappel ordonné** = longueur exacte de la plus longue sous-séquence commune (LCS) / taille de la référence. Le calcul est bit-parallèle avec des masques d’entiers bornés par 5 000 tokens ; il évite la matrice quadratique et a une couverture de régression exhaustive sur toutes les séquences binaires de longueur 0 à 4.

Le rapport expose les mots extraits, les mots correspondants et les mots supplémentaires, avec les mesures globales, par format et les pires cas. Il ne contient aucun texte documentaire ni nom/chemin de fichier.

## Portée et limites

L’ordre V544 compare l’ordre des phrases d’annotation déclaré avec l’ordre de traversée des paragraphes, cellules et zones de texte OOXML. Ce score **n’est pas** une mesure de l’ordre de lecture visuel humain ; l’ordre réel peut varier avec la géométrie des pages, les colonnes, les zones flottantes et les tableaux. La fidélité visuelle, la typographie, la géométrie des tableaux, les styles, les images, les formules et la sémantique restent non évalués.

La provenance `human_reviewed` est déclarative et non authentifiée. Les tests ci-dessous utilisent des documents synthétiques connus à leur génération ; ils ne démontrent pas une précision sur corpus métier.

## Sécurité et bornes

Les précontrôles V542 restent actifs : SHA-256 des sources/résultats/annotations, limites OOXML/ZIP, refus de liens et de traversals, contenu actif, relations externes, doublons et mutation en cours d’analyse. La voie étendue borne à 5 000 tokens par document et 50 000 tokens observés sur un corpus, afin d’éviter un coût non borné. L’export de reçu conserve la liste blanche et refuse l’écrasement.

Les anciennes manifestations V542 demeurent en schéma V1. Les manifestes qui incluent les trois seuils étendus produisent un rapport V2. La GUI accepte les deux et affiche les métriques V544 uniquement quand elles sont présentes.

## Qualification automatisée

Le workflow V544 s’exécute sur Ubuntu 24.04 et Windows Server 2022 pour les tests fonctionnels, compilation Python, sécurité et régressions V542/V543/V539. Un job Linux Xvfb exerce également le véritable dialogue Tk, le traitement asynchrone et l’export. Ces contrôles CI ne constituent pas une qualification graphique humaine Windows.

Cas de régression principal : une référence `Alpha Beta Gamma` et un document `Extra Alpha Gamma Beta` échouent sur précision/ordre. V544.1 corrige aussi un défaut du balayage glouton initial : pour la référence `Alpha Beta Gamma` et la sortie `Beta Gamma Alpha`, la LCS exacte vaut deux tokens (2/3), pas un (1/3).

## Auteur et statut

**Auteur : Abdelhalim Talbi.** Version applicative de base conservée à 51.4 ; V544 est une évolution de qualification sur une branche dédiée. Aucun merge automatique vers `main`.


## Correctif V544.1 — exactitude du rappel ordonné

Un audit du calcul a révélé que le parcours glouton des mots de référence ne calculait pas toujours la plus longue sous-séquence commune. Le contre-exemple `A B C` / `B C A` donnait 1/3 alors que deux mots peuvent être conservés dans l’ordre. Le moteur utilise désormais une récurrence LCS bit-parallèle exacte, et les tests la comparent à un oracle de programmation dynamique sur 930 paires de séquences courtes. Cette correction change la mesure de l’ordre, sans prétendre évaluer l’ordre visuel des pages.
