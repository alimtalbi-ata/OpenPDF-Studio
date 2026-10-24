# OpenPDF Studio V525 — Corpus PDF→Excel sans doublons

**Auteur : Abdelhalim Talbi** · **24 octobre 2026** · Version applicative **V51.4**.

## Correction
Le gate `openpdf_xlsx_corpus_gate_v519.py` rejette maintenant les cas ayant des empreintes SHA-256 PDF ou XLSX déjà rencontrées, même lorsque les chemins sont différents. Sans ce contrôle, les doublons pouvaient gonfler artificiellement la couverture et les mesures de fidélité.

## Qualification reproductible
- 109 tests Excel locaux Linux réussis sur 109.
- 3 tests V525 : trois PDF synthétiques réellement convertis (tableau bordé avec formule littérale, tableau sans bordures multipages, page mixte).
- 5 tableaux, 54 cellules non vides exactes, 0 cellule inventée, 0 cas annoté humainement.
- Mutation de cellule : le gate échoue. Duplication PDF/XLSX : rejet.
- CI GitHub Actions du commit fonctionnel V525 : 9/9 jobs PASS (Excel Ubuntu/Windows 2/2, métadonnées 2/2, source et Windows natif 5/5).

## Limites
Ce corpus est **synthétique**, sans annotation humaine et sans mesure de fidélité visuelle. Le rejet repose sur l'identité binaire SHA-256 et ne détecte pas les quasi-doublons sémantiques. Aucune qualification graphique humaine Windows n'est revendiquée.

## Livraison
Les fichiers Word/PDF et le corpus de preuve sont inclus dans le ZIP cumulatif V525. Les exécutables Windows V51.4 ont été reconstruits depuis le commit fonctionnel V525 ; les preuves natives de lancement, OCR, installation et désinstallation sont intégrées au ZIP. Le nouveau gate Python V525 n'est pas embarqué dans les exécutables. Ne pas confondre tests CI et validation utilisateur graphique.

**PR :** https://github.com/alimtalbi-ata/OpenPDF-Studio/pull/32
