# OpenPDF Studio V541 — Qualification OCR accessible dans l'interface

**Auteur : Abdelhalim Talbi — 25 octobre 2026**

## Fonction

Un bouton **Qualité OCR** ouvre un dialogue local dans l'application Windows. L'utilisateur choisit un manifeste JSON de corpus de référence V539/V540, déclenche une analyse asynchrone, puis peut exporter un reçu JSON. Le dialogue reste réactif pendant la lecture des PDF. Le moteur existant vérifie SHA-256, références et seuils CER/WER globaux, par document et facultativement par page.

L'interface affiche **PASS/FAIL**, CER, WER, compteurs et seuils échoués, sans afficher de texte OCR, de nom de document ni de chemin. Le reçu exporté applique une liste blanche stricte : aucune clé arbitraire issue d'une preuve non fiable ne peut être exposée. La sortie est créée exclusivement (`x`) : aucun écrasement d'un fichier existant. Les erreurs d'évaluation sont affichées de façon générique pour éviter la divulgation de chemins.

## Utilisation

1. Préparer un manifeste conforme au format `openpdf.ocr.reference.corpus.v1` (voir documentation V539 et V540).
2. Ouvrir **Qualité OCR**, sélectionner le manifeste JSON et choisir **Analyser**.
3. Consulter les mesures, puis **Exporter le reçu** dans un nouveau fichier si nécessaire.

La qualification ne modifie ni les PDF sources ni les PDF OCR. Les références `human_reviewed` restent déclaratives, non authentifiées. Un rapport PASS ne certifie **ni fidélité visuelle ni fidélité Word/Excel/PowerPoint**. Les mesures reposent sur la couche texte sérialisée des PDF et les annotations fournies.

## Qualification et limites

- Tests unitaires V541 : validation des champs, valeurs finies, types exacts, SHA-256, non-divulgation et intégration statique du dialogue.
- Test graphique Linux sous Xvfb : ouverture réelle de la fenêtre et du dialogue, sans interaction humaine.
- CI Ubuntu/Windows : tests statiques et de logique ; ne remplace pas une validation interactive Windows du portable/installeur.
- Une compilation Windows V541 et sa signature Authenticode restent à confirmer par les campagnes de build. Aucun exécutable historique ne doit être présenté comme compilé depuis V541.

## Architecture

```text
GUI Tkinter (OpenPDFStudio) -> thread de qualification -> moteur V539/V540
               |                                      |
               +-> file de messages -> filtrage V541 <-+
                           |
                  synthèse et reçu JSON sans texte
```

## Prochaine priorité

Qualification interactive Windows avec scénarios utilisateur, puis corpus métier annoté indépendamment pour mesurer les écarts OCR et la fidélité Office éditable.
