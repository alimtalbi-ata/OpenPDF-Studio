# OpenPDF Studio V51.4 — Extraction Excel éditable et finalisation GUI

**Auteur : Abdelhalim Talbi — 24 octobre 2026**

## Fonctionnel

La conversion PDF → XLSX conserve la feuille historique `Texte PDF`. Le mode optionnel « Tableaux en feuilles Excel éditables » crée une feuille par tableau détecté, avec provenance page/tableau et comparaison cellule par cellule avant publication. L'interface n'active jamais cette option implicitement. Les cellules ressemblant à des formules restent des chaînes littérales, jamais exécutées.

Le dispatcher de l'interface passe par le mécanisme de réservation et d'audit existant. Il refuse les destinations existantes et les liens symboliques, ainsi que la combinaison du mode tableaux et du pipeline OCR Office. Pour un PDF numérisé, effectuer un OCR PDF séparé avant la conversion Excel.

## Livraison Windows

`BUILD-OPENPDF-WINDOWS.cmd` reste le point d'entrée unique. `VERSION.txt` indique **51.4**. Le manifeste V51.4 contrôle 94 modules ; la recette Inno V51.4 et les workflows de compilation Windows exigent des exécutables, reçus et noms de version cohérents. Les binaires V51.3 historiques présents dans le candidat source ne doivent jamais être annoncés comme des binaires V51.4.

## Qualification et limites

Les tests de routage GUI/dispatcher, d'intégrité, de conversion PDF synthétique réelle, de compatibilité OCR et de sécurité sont séparés de la qualification graphique. Une capture de l'interface sous **Linux Xvfb** peut figurer dans l'archive, explicitement étiquetée ; elle n'est pas une preuve Windows. L'extraction PyMuPDF reste heuristique, notamment pour les tableaux sans bordures et les cellules fusionnées. Les conversions Office ne garantissent pas la fidélité des styles et des dimensions d'origine. Les exécutables ne sont pas signés Authenticode.

**Prochaine priorité :** qualification Windows V51.4 effective, mesure de fidélité sur un corpus métier, détection de tableaux sans bordures et de cellules fusionnées.
