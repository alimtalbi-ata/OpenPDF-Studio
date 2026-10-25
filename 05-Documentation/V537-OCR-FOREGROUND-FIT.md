# OpenPDF Studio V537 — Rotation OCR : conservation de la résolution utile

**Auteur : Abdelhalim Talbi.** Base : V536 (PR #43). Aucun merge automatique.

## Problème reproduit

La V536 évite la coupe des contenus aux bords en tournant la page sur un canevas étendu puis en ajustant **tout** le canevas à la taille d'origine. Les coins blancs introduits par la rotation forcent un sous-échantillonnage inutile des caractères lorsque seuls quelques éléments touchent un bord.

## Correction

`rotate_ocr_canvas` conserve le parcours rapide V536 si la boîte du contenu tient dans la page. Dans le cas contraire, la rotation étendue est suivie d'une détection prudente des pixels non blancs (luminance < 250), d'une marge de quatre pixels, puis d'un ajustement uniforme **de la seule zone utile**. La taille de sortie reste identique à la taille d'entrée, sans étirement anisotrope. L'image source n'est pas modifiée.

L'amélioration s'applique aux redressements OCR manuel et automatique existants, sans changer la CLI ni les options utilisateur. Les limites de pixels et les contrôles d'angle V536 restent en place.

## Tests exécutés localement (Linux)

- V537 : **5/5** tests synthétiques PASS, dont comparaison avec l'algorithme de redimensionnement V536, conservation des quatre coins, immutabilité de la source et contrôle du budget.
- V536 : **9/9** PASS, dont OCR réel de PDF synthétiques inclinés vers XLSX éditable.
- V535 : **12/12** PASS ; V534 : **7/7** PASS ; V533 : **8/8** PASS.
- Total des cinq suites : **41/41 PASS**.
- Une image synthétique localisée en coin montre une augmentation supérieure à 40 % du nombre de pixels sombres par rapport à l'ajustement de tout le canevas. Cette métrique **n'est pas** une mesure de précision OCR.

## Risques et limites

- Les documents métier annotés indépendamment restent à évaluer ; les pixels sombres ne sont pas une preuve de fidélité sémantique.
- Une page avec fond non blanc peut conduire à un ajustement conservateur proche de celui de V536.
- L'interface Windows n'a pas fait l'objet d'un test humain interactif ; la CI Windows doit être vérifiée séparément.
- Aucune signature Authenticode nouvelle n'est revendiquée.

## Prochaine priorité

Évaluer l'exactitude OCR sur un corpus métier annoté (CER, WER, précision/rappel des tableaux), puis corriger les écarts prioritaires.
