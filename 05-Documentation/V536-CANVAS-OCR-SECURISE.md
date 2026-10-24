# OpenPDF Studio V536 — Redressement OCR sans rognage silencieux

**Auteur : Abdelhalim Talbi** · **Base : V535 / PR #42** · **Livraison : PR #43 en brouillon**

## Défaut reproduit
Le redressement raster précédent utilisait Pillow `rotate(..., expand=False)`. Sur un scan avec éléments proches des quatre coins, cette rotation supprimait des pixels d'origine. Exemple de fixture synthétique 800 × 500, quatre marqueurs noirs et angle −12° : environ 2 420 pixels sombres conservés avec l'ancienne rotation, contre plus de 7 300 avec la nouvelle (seuil de comptage <160/255, valeurs dépendant de Pillow).

## Correction
`openpdf_ocr_canvas_v536.rotate_ocr_canvas` examine la boîte englobante du premier plan :
1. Si le contenu reste entièrement dans la page après rotation, l'ancien rendu à résolution native est conservé (pas de rééchantillonnage inutile).
2. Si le contenu risque de sortir du cadre, la rotation se fait avec `expand=True`, puis le raster est remis à l'échelle **uniformément**, centré sur un fond blanc de mêmes dimensions.
3. Les angles non finis, hors ±12°, les booléens et les dépassements de budget de pixels sont refusés.

La protection est utilisée dans `searchable_pdf`, donc par l'OCR manuel et automatique et les conversions Office éditables. Aucun contenu n'est transmis à un service distant.

## Régression détectée et corrigée pendant V536
Une première implémentation appliquait systématiquement la remise à l'échelle. Sur un PDF synthétique de tableau, le texte « A02 » était reconnu « Ad2 » en mode manuel. L'algorithme a été corrigé pour préserver la résolution native quand la page possède des marges suffisantes. Les tests OCR réels repassent ensuite.

## Tests
- V536 : **9/9 tests locaux Linux réussis**, dont deux conversions OCR réelles de PDF synthétiques vers XLSX éditable, avec vérification des 12 cellules pour le mode manuel.
- Régressions ciblées V535 : 12/12 ; V534 : 7/7 ; V533 : 8/8 ; V532 : 4/4.
- Compilation statique Python des sources modifiées : réussie.
- CI Windows/Linux : vérifier le statut du commit de la PR #43 ; les jobs ne remplacent pas une qualification graphique humaine.

## Limites et risques
La remise à l'échelle peut diminuer la taille des caractères si des éléments sont en bordure. Le seuil de premier plan est une heuristique et ne garantit ni exactitude OCR ni fidélité métier. Les tests sont **synthétiques** et ne constituent pas un corpus métier annoté indépendamment. L'interface Windows n'a pas été testée manuellement. Le portable et l'installateur ont été reconstruits sur runner Windows depuis le commit fonctionnel V536 `afc31101` (2/2 jobs PASS, autocontrôles et installation/désinstallation silencieuses). Les deux commits suivants modifient uniquement le test de réconciliation et le manifeste SHA-256 ; le code runtime est identique (comparaison GitHub vérifiée).

## Priorité V537
Constituer un corpus métier légalement partageable et annoté indépendamment ; mesurer précision/rappel de reconnaissance, puis comparer les conversions Word, Excel et PowerPoint. Qualifier l'interface Windows interactive et les installateurs reconstruits à partir du commit final.
