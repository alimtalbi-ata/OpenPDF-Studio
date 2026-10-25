# OpenPDF Studio V543 — Qualité Office dans l'interface graphique

**Auteur : Abdelhalim Talbi** · **Socle applicatif : V51.4** · **25 octobre 2026**

## Objectif

L'évaluateur de fidélité éditable V542 était uniquement accessible en CLI. V543 ajoute **Qualité Office** à l'en-tête de l'interface Tkinter, sans modifier les conversions existantes.

Le dialogue sélectionne un manifeste local V542, évalue en arrière-plan les DOCX/XLSX/PPTX avec `evaluate_office_reference_corpus`, affiche un bilan agrégé par format et exporte un reçu JSON par création exclusive. Le fichier de sortie préexistant n'est jamais écrasé. L'interface ne reprend ni contenu, ni noms, ni chemins des documents analysés dans le bilan ou le reçu. Le chemin du manifeste est visible dans son champ de sélection.

## Mesures et limites

La mesure porte sur le **rappel multiensemble des mots contenus dans des objets Office éditables**. Une image du texte sans objets natifs ne satisfait pas le contrôle. Les seuils sont ceux du manifeste V542, avec refus sur erreur. La provenance humaine des annotations est déclarative, **non authentifiée**. La précision (mots supplémentaires), l'ordre de lecture, les styles, la géométrie des tableaux et la fidélité visuelle **ne sont pas mesurés**. Aucun corpus métier indépendant n'a été qualifié.

## Utilisation

1. Constituer au moins deux cas selon le schéma `openpdf.office.reference.corpus.v1` documenté en V542, avec PDF sources, fichiers Office et annotations liées par SHA-256.
2. Dans OpenPDF Studio, ouvrir **Qualité Office**, sélectionner le `manifest.json`, puis **Analyser**.
3. Examiner PASS/FAIL, le rappel global, le pire cas, les seuils échoués et la ventilation DOCX/XLSX/PPTX.
4. Exporter le reçu JSON dans un **nouveau fichier**. Aucun texte métier n'y figure.

La qualification ne convertit pas automatiquement les PDF : elle inspecte les sorties Office existantes. Elle ne publie ni ne modifie les documents d'entrée.

## Architecture

```text
GUI Tkinter (bouton Qualité Office)
  └── Thread asynchrone, queue de résultat
       └── openpdf_office_reference_v542.evaluate_office_reference_corpus
            ├── vérifications PDF, OOXML, SHA-256 et budgets
            └── rappel des mots réellement éditables
       └── openpdf_office_quality_ui_v543.safe_office_receipt
            ├── schéma, compteurs, seuils et cohérence des taux
            └── liste blanche de champs non sensibles
  └── affichage agrégé / export JSON exclusif
```

## Qualification locale V543

- **10 tests V543 sous Xvfb : PASS**, dont un dialogue Tk réel (asynchronisme, export et refus d'écrasement).
- **12 tests V542 : PASS** ; **8 tests V541 : PASS**.
- **Compilation Python : PASS**.
- **Source closure statique : PASS**, 101 modules scannés, manifeste V51.4 complété.
- Une capture **Linux Xvfb réelle** est jointe à l'archive de livraison. Elle ne représente **pas** une capture Windows.
- **Compilation Windows native, installation/désinstallation, CI distante et validation humaine Windows : à vérifier séparément**. Aucun succès Windows ne doit être déduit du seul passage des tests Linux.

## Risques et suite

La GUI nécessite la présence des dépendances du moteur V542 dans le paquet Windows ; la CI native doit le vérifier. Le bilan ne prouve ni la fidélité de mise en page, ni l'absence de texte ajouté. Prochaine priorité : mesure de précision et ordre de lecture sur un corpus annoté indépendamment, puis qualification interactive Windows.

Aucun secret dans les rapports ; aucune fusion automatique de la branche de travail vers `main`.
