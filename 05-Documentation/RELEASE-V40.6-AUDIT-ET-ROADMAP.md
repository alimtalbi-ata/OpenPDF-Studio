# OpenPDF Studio V40.6 — Consolidation des entrées et sorties
Auteur : Abdelhalim Talbi

## Diagnostic technique
Le contrôle de destination existante était réalisé tardivement dans le moteur. La validation UI ne bloquait pas immédiatement le risque de collision; l'utilisateur attendait parfois le lancement du traitement avant de recevoir une erreur. La liste des sources vérifiait les chaînes brutes, ce qui laissait passer certains chemins équivalents.

## Modifications V40.6
1. Validation anticipée des collisions de destination, sans écrasement.
2. Contrôle explicite des extensions PDF et Office.
3. Déduplication des chemins normalisés à l'import.
4. Tests avec véritables fichiers temporaires pour vérifier le refus d'écrasement et l'absence de modification.
5. Packaging Windows cumulatif versionné et manifestes SHA-256.
6. Préservation des contrats de raccourcis V40.5.

## Limites de preuve
La CI vérifie la compilation, les tests et le packaging. Elle ne démontre ni une inspection humaine réelle de toutes les pages Windows ni la fidélité de conversion Office sur un corpus de référence. Les manuels Word/PDF historiques présents ne sont pas déclarés actualisés pour V40.6.

## Roadmap pilotée par risques
- V40.7 : corpus de fidélité PDF→DOCX/XLSX/PPTX, tableaux, images, polices et OCR; score par document.
- V40.8 : journal d'audit JSON, reprise après interruption, tests de panne disque et restauration.
- V40.9 : test Windows propre (installateur + portable), DPI, accessibilité et captures réelles.
- V41.0 : interface guidée par tâches, batch et préréglages, profils reproductibles et documentation Word/PDF approfondie.
