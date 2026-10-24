# OpenPDF Studio V51.4 / V523 — Extraction de tableaux mixtes PDF → XLSX

**Auteur : Abdelhalim Talbi** — 24 octobre 2026.

## Objectif et problème reproduit
V522 n'activait la détection de tableaux sans bordures que lorsqu'aucun tableau géométrique n'était présent sur la page. Un document avec une grille bordée et un tableau aligné sans traits sur la même page produisait un XLSX incomplet. La tentative expérimentale V523 échouait également car le PDF de test dessinait des rectangles indépendants que PyMuPDF ne reconnaissait pas comme une grille continue.

## Correction
1. Préserver les tableaux bordés retournés par `page.find_tables()`.
2. Soustraire leur emprise (marge de 2 points) à la page et générer des régions rectangulaires disjointes. Limiter à 64 régions, sinon refuser la conversion enrichie.
3. Détecter les tableaux textuels uniquement dans les régions libres, jamais dans les tableaux bordés. Refuser un chevauchement résiduel.
4. Séparer les blocs de texte par les grandes discontinuités verticales avant d'inférer des colonnes. Cela évite qu'un paragraphe éloigné transforme une grille de 3 colonnes en 8 colonnes fictives.
5. Conserver les garde-fous V522 : au moins trois lignes denses, colonnes alignées, gouttières visibles, cellules non tronquées, absence de formules exécutables et vérification XLSX après écriture.

## Architecture
```text
PDF source (empreinte SHA-256 et contrôle d'immuabilité)
  -> détection géométrique des tableaux bordés
  -> partition spatiale de la page hors zones bordées
  -> séparation verticale des blocs textuels éloignés
  -> extraction prudente des grilles sans bordures
  -> vérification des chevauchements et limites de ressources
  -> feuilles XLSX éditables + provenance page/tableau
  -> audit cellule par cellule et publication atomique
```

## Qualification effectuée localement (Linux)
- 102 tests `test_xlsx_*.py` : **PASS**, dont 7 nouveaux tests V523.
- PDFs synthétiques réellement créés et convertis : deux tableaux superposés ou côte à côte, 24 cellules vérifiées par cas.
- Non-régression : prose éloignée, formule Excel conservée comme chaîne, corruption de cellule rejetée, fragmentation spatiale excessive refusée.
- Exécution : `python -m unittest discover -s 04-Tests-et-Qualification -p 'test_xlsx_*.py' -v`.

## Limites / risques
- La fidélité des documents métiers réels et la précision sémantique des cellules ne sont pas établies par des PDF synthétiques.
- Une grille non reconnue par PyMuPDF reste non reconnue ; la correction ne remplace pas l'OCR.
- Les tableaux chevauchant une zone bordée ou franchissant une partition spatiale peuvent être omis.
- La détection textuelle reste heuristique ; aucun taux de rappel réel n'est revendiqué.
- Qualification Windows et CI à confirmer pour chaque commit ; aucune qualification humaine de l'interface ni signature Authenticode.

## Politique de publication
PR brouillon empilée sur V522, sans fusion automatique. Le numéro de version de l'application demeure 51.4. Les exécutables Windows V522, s'ils sont repris dans un ZIP cumulatif, ne constituent pas des binaires V523 qualifiés.
