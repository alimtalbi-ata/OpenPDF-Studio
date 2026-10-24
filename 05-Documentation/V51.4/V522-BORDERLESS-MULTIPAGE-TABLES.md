# OpenPDF Studio V522 — Tableaux sans bordures, PDF multipages

**Auteur : Abdelhalim Talbi**  
**Base : OpenPDF Studio 51.4 / qualification V521**  
**Date : 24 octobre 2026**

## Problème et comportement corrigé

La conversion PDF vers Excel en mode tableaux utilisait uniquement la stratégie géométrique `lines` de PyMuPDF. Les tableaux sans traits étaient souvent ignorés, conduisant à un refus de publication alors que les données étaient visiblement organisées en colonnes. Le moteur V522 ajoute une stratégie de secours `text` uniquement pour les pages où aucun tableau à bordures n'a été trouvé. Les tableaux sont traités page par page, chaque feuille conservant sa provenance `Pxxxx-Txxx`.

## Mesures de sûreté et compromis

La stratégie `text` peut confondre texte aligné et tableau. Pour limiter les faux positifs, V522 exige au moins trois lignes et deux colonnes alimentées, une occupation minimale de 75 %, au moins trois valeurs par colonne, ainsi que des espaces visuels d'au moins 12 points entre colonnes adjacentes. Les lignes d'espacement entièrement vides sont supprimées. Un titre de page isolé n'est ignoré que s'il est nettement séparé du tableau. Aucun merge n'est déduit de la seule disposition du texte. Si la stratégie `lines` a trouvé un tableau, elle reste prioritaire pour cette page : les tableaux mixtes sur une même page ne sont donc pas tous garantis.

L'option reste **désactivée par défaut**. Les protections existantes restent actives : limite de tableaux/cellules, refus des formules actives, audit XLSX avant publication, non-écrasement et vérification après sauvegarde. L'extraction des valeurs ne démontre pas la fidélité visuelle, ni la justesse sémantique sur des documents réels.

## Qualification reproductible

```bash
python -m unittest discover -s 04-Tests-et-Qualification -p test_xlsx_borderless_v522.py -v
python -m unittest discover -s 04-Tests-et-Qualification -p test_xlsx_tables_v514.py -v
```

Le jeu V522 génère **réellement** des PDF synthétiques multipages avec tableaux sans bordures, convertit en XLSX éditable, contrôle 24 cellules sur deux pages et vérifie les formules littérales, le rejet des faux tableaux de prose, le rejet des grilles trop courtes, l'absence d'effet en mode historique et la détection d'une cellule altérée. Il ne s'agit **pas** de captures réelles d'une interface Windows, ni d'un corpus annoté par des humains.

## Architecture et limites

```text
PDF source -> PyMuPDF page.find_tables(lines)
                      | si aucun tableau sur la page
                      +-> find_tables(text) -> densité + gouttières >=12pt
                      |                             -> retrait des lignes vides
                      +-> cellules/merges fiables -> feuilles Excel éditables
                      -> audit source / XLSX -> vérification -> publication atomique
```

Risques résiduels : textes alignés pouvant encore être confondus avec des tableaux, tableaux mixtes bordés/non bordés sur la même page, scans sans OCR, cellules fusionnées sans traits, documents métier non représentés et validation GUI Windows humaine non réalisée. Les exécutables Windows V51.4 déjà présents dans le ZIP historique **ne contiennent pas V522** tant qu'une nouvelle compilation native CI n'a pas été qualifiée.
