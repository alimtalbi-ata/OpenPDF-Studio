# OpenPDF Studio V540 — Seuils OCR indépendants par page

**Auteur : Abdelhalim Talbi — 25 octobre 2026**

## Défaut reproduit et correction

Le contrôle V539 évaluait les CER/WER globaux et par document. Un PDF de plusieurs pages pouvait satisfaire les seuils moyens alors qu'une page numérisée ne contenait **aucun texte OCR**. V540 introduit deux seuils optionnels, `max_page_cer` et `max_page_wer`, contrôlés avant tout arrondi. Si une page dépasse l'un des deux, le rapport signale `page_quality_floors` et le processus retourne le code `3`.

Les deux paramètres doivent être déclarés ensemble. Les anciens manifestes V539 restent acceptés sans changement de comportement. Le nouveau rapport inclut uniquement des statistiques agrégées : `pages_below_quality_floors`, `worst_page_cer`, `worst_page_wer` et `page_quality_floors_enabled`. Il ne révèle ni texte ni nom de document. Une page sans référence non vide ne permet pas une mesure par page et est refusée lorsque les seuils sont activés.

## Configuration

Dans le manifeste V539 (`openpdf.ocr.reference.corpus.v1`), compléter `thresholds` avec :

```json
{
  "max_cer": 0.10,
  "max_wer": 0.20,
  "max_case_cer": 0.20,
  "max_case_wer": 0.30,
  "min_human_reviewed": 0,
  "max_page_cer": 0.25,
  "max_page_wer": 0.35
}
```

Les deux derniers seuils sont facultatifs mais indissociables. `min_human_reviewed: 0` ne signifie **pas** que les références ont été revues par un humain. Pour un corpus métier contrôlé, définir un seuil non nul et documenter la provenance indépendamment.

Exécution :

```powershell
python 03-Sources/openpdf_ocr_reference_corpus_v539.py --manifest C:\corpus\manifest.json --report C:\corpus\resultat-v540.json
```

Codes : `0` = seuils respectés ; `3` = échec de fidélité ; `2` = entrée/preuve invalide ou rapport déjà existant. Les sorties sont créées sans écrasement.

## Qualification et limites

Les tests V540 utilisent de **vrais fichiers PDF synthétiques sérialisés**, avec couche texte volontairement absente sur la seconde page, et une référence produite indépendamment de la couche OCR. Les seuils globaux/par document acceptent le cas ; les nouveaux seuils par page le refusent. Aucun texte métier, aucun document client et aucune capture Windows simulée ne sont fournis.

La preuve porte uniquement sur la couche texte extractible ; elle ne mesure pas la fidélité visuelle, la structure des tableaux ni la qualité des conversions Office. La vérification interactive Windows et la signature Authenticode restent à faire. Le module de qualification V539/V540 reste un **outil Python CLI autonome**, non intégré à la GUI Windows. Aucun changement des exécutables n'est revendiqué.

## Priorité suivante

Intégrer la qualification dans le flux UI Windows sans exposer les textes métier, puis mesurer CER/WER sur un corpus métier annoté par des tiers, avec provenance contrôlée.
