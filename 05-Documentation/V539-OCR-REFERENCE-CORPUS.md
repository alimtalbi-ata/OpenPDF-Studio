# OpenPDF Studio V539 — Corpus OCR de référence

**Auteur : Abdelhalim Talbi — 25 octobre 2026**

## Fonctionnalité

La commande `openpdf_ocr_reference_corpus_v539.py` compare la couche texte de PDF OCR réels à des références indépendamment rédigées. Elle réutilise la distance de Levenshtein du module `openpdf_ocr_quality_v487.py` et calcule les taux d'erreur de caractères (CER) et de mots (WER) **sur les nombres d'erreurs exacts**, sans arrondir les décisions. Les mesures globales et par document empêchent un bon document de masquer un échec local.

Le contrôle vérifie la correspondance SHA-256 des annotations avec le PDF source, les empreintes de tous les fichiers avant et après évaluation, l'absence de chemins traversants, de liens symboliques, de clés JSON dupliquées, de cas identiques et de références mal alignées. Des limites de taille, de pages et de coût quadratique protègent le poste Windows. Le rapport ne contient ni noms de documents ni texte extrait.

## Utilisation

```powershell
python 03-Sources/openpdf_ocr_reference_corpus_v539.py --manifest C:\corpus\manifest.json --report C:\corpus\qualite.json
```

Exemple **illustratif** de manifeste :

```json
{
  "schema": "openpdf.ocr.reference.corpus.v1",
  "cases": [
    {"id":"document-a","source_pdf":"a-scan.pdf","ocr_pdf":"a-ocr.pdf","annotations":"a-reference.json"},
    {"id":"document-b","source_pdf":"b-scan.pdf","ocr_pdf":"b-ocr.pdf","annotations":"b-reference.json"}
  ],
  "thresholds": {
    "max_cer": 0.05,
    "max_wer": 0.10,
    "max_case_cer": 0.10,
    "max_case_wer": 0.20,
    "min_human_reviewed": 2
  }
}
```

Chaque annotation suit `{"schema":"openpdf.ocr.reference.v1","source_sha256":"<sha256 source>","origin":"human_reviewed","pages":[{"page":1,"text":"texte de référence saisi indépendamment"}]}`. Le champ `origin` est une déclaration : le logiciel **ne prouve pas** la réalité d'une validation humaine. Pour les tests synthétiques, utiliser `synthetic_known_at_generation`.

## Portée de la preuve et limites

- CER = distance d'édition en caractères / caractères de référence. WER = distance d'édition en mots / mots de référence. Les valeurs peuvent dépasser 1 si de nombreuses insertions surviennent.
- Comparaison de la couche texte extraite des PDF sérialisés. Elle ne prouve ni la provenance de la reconnaissance, ni la fidélité visuelle, ni la structure des tableaux Word/Excel/PowerPoint.
- Corpus V539 : deux cas synthétiques avec vrais PDF et couches texte, plus deux conversions réelles par Tesseract en anglais. **Aucun corpus métier annoté par un humain n'a été fourni.**
- Qualification Windows : les tests Python de lecture et comparaison de PDF peuvent tourner sous Windows CI ; aucune qualification graphique humaine ou recompilation de l'installateur V539 n'est revendiquée.

## Sécurité et codes retour

`0` : seuils respectés ; `3` : écarts mesurés ; `2` : preuve invalide ou sortie existante. Le rapport JSON est créé exclusivement, sans écrasement. Les PDF source et OCR ne sont jamais modifiés.

## Prochaine priorité

Importer un corpus métier annoté par un tiers, évaluer séparément les scans inclinés, multipages et multilingues, puis corriger les cas à plus fort CER/WER. Intégrer le contrôle à l'interface Windows après validation produit.
