# OpenPDF Studio V542 — Qualification de la fidélité Office éditable

**Auteur : Abdelhalim Talbi — 25 octobre 2026**

## Changement produit

`03-Sources/openpdf_office_reference_v542.py` mesure le **rappel des mots réellement présents dans des éléments éditables** DOCX, XLSX et PPTX par rapport à des références distinctes, liées par SHA-256 au PDF source. Il refuse les sorties uniquement constituées d'images lorsque le seuil de contenu éditable est activé. Le reçu agrégé ne contient ni texte, ni nom, ni chemin de document.

## Manifeste de qualification

Le manifeste `openpdf.office.reference.corpus.v1` contient entre 2 et 32 cas, chacun avec `id`, `source_pdf`, `office_file`, `annotations`. L'annotation `openpdf.office.reference.v1` contient `source_sha256`, `origin` (`human_reviewed` ou `synthetic_known_at_generation`) et `expected_phrases` (liste de textes de référence). Les quatre seuils sont obligatoires : `min_token_recall`, `min_case_token_recall` (0 à 1), `min_human_reviewed`, `min_editable_elements_per_case`.

Exécution : `python 03-Sources/openpdf_office_reference_v542.py CORPUS/manifest.json --receipt CORPUS/rapport-nouveau.json`. Codes retour : 0=PASS, 2=FAIL qualité, 3=ERROR. Le rapport est créé exclusivement et n'écrase aucun fichier existant.

## Portée exacte

Le contrôle vérifie de véritables paragraphes Word, cellules Excel et zones de texte PowerPoint. Le **rappel multiensemble de tokens** normalise Unicode NFKC et la casse, sans confondre deux occurrences d'un même mot. Les décisions utilisent les valeurs non arrondies.

**Non mesurés :** précision des mots supplémentaires, ordre de lecture, typographie, positionnement, géométrie des tableaux, cellules fusionnées, images, fidélité visuelle et exactitude des caractères OCR. Un rappel de 100 % n'est pas une certification de conversion fidèle. La provenance humaine est déclarative et non authentifiée. Les références synthétiques ne constituent pas un corpus métier indépendant.

## Sécurité

PDF source lisible et non chiffré, SHA-256 des entrées, budget ZIP/OOXML, refus de traversal, liens, membres dupliqués, macros, ActiveX/OLE, relations externes, archives excessives, seuils invalides et fichiers modifiés pendant l'analyse. Aucun contenu actif n'est exécuté.

## Qualification

12 nouveaux tests déterministes dont **conversion réelle OpenPDF** de trois PDF synthétiques vers DOCX, XLSX et PPTX, et mesure de **12/12 tokens** dans les objets Office éditables. Les tests négatifs couvrent image seule, perte de texte, macros, ZIP traversal, relation externe, empreinte source erronée et export sans écrasement. Régressions OCR V539–V541 : 32/32 PASS local Linux. Les résultats Windows CI sont à vérifier après publication. Aucun test graphique humain Windows n'est revendiqué.

## Prochaine priorité

Intégration dans la GUI Windows, corpus métier annoté indépendamment, métriques de précision et géométrie, scénarios Office complexes, puis reconstruction et qualification interactive des binaires Windows V542.
