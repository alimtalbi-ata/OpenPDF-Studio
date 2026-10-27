# OpenPDF Studio V51.4 / V558 - Fidelite visuelle PDF / Office

Auteur : Abdelhalim Talbi. V558 est un jalon de developpement ; le numero applicatif reste 51.4.

## Objet

V558 ajoute un audit local comparant un PDF source a un PDF de rendu fourni pour le candidat DOCX, XLSX ou PPTX. L'evaluation combine quatre familles de controles :
- raster en niveaux de gris a 96 dpi : erreur absolue moyenne et fraction de pixels modifies ;
- forme des pages : nombre et dimensions physiques ;
- geomerie : derive des centres et intersection-over-union (IoU) des boites de mots extraites ;
- contenu extrait : precision, rappel et rappel d'ordre par LCS exacte (V544).

Cette combinaison n'est pas une certification de fidelite metier. L'ordre mesure est celui du texte extrait, et non l'ordre de lecture visuel humain.

## Parcours d'utilisation

1. Convertir un document Office en PDF avec un moteur Office disponible.
2. Preparer un manifeste conforme au schema ci-dessous, dans un dossier contenant les preuves.
3. Depuis OpenPDF Studio, ouvrir **Fidelite Office**, selectionner le manifeste et lancer l'analyse. Le calcul s'execute sur un worker separe de l'interface.
4. Examiner les seuils en echec et, si necessaire, exporter un recu agrege JSON sans contenu PDF ni chemins.
5. Conserver les fichiers sources et versions du moteur avec le manifeste si le resultat doit etre reproduit.

Le programme ne lance pas Microsoft Office ou LibreOffice pour produire le PDF de rendu. Le nom et la version du moteur sont declares dans l'annotation et ne sont ni signes ni attestes par le programme.

## Schema du manifeste

Le manifeste contient exactement les proprietes `schema`, `cases` et `thresholds`. Il doit inclure de 2 a 32 cas.

```json
{
  "schema": "openpdf.office.visual-fidelity.corpus.v558",
  "cases": [
    {
      "id": "contrat-001",
      "source_pdf": "source.pdf",
      "office_file": "conversion.docx",
      "rendered_pdf": "conversion-rendu.pdf",
      "annotations": "contrat-001.json"
    }
  ],
  "thresholds": {
    "max_page_count_delta": 0,
    "max_page_dimension_delta_pct": 1.0,
    "max_mean_abs_pixel_error": 8.0,
    "max_changed_pixel_fraction": 0.02,
    "min_text_precision": 0.95,
    "min_text_recall": 0.95,
    "min_ordered_token_recall": 0.95,
    "max_mean_word_center_drift_pct": 1.0,
    "min_mean_word_box_iou": 0.9,
    "min_human_reviewed": 0
  }
}
```

L'exemple est illustratif et ne constitue pas une preuve. Le schema valide 2 a 32 cas : ajouter au moins un deuxieme cas avant utilisation. Toutes les valeurs numeriques doivent etre finies ; un bool n'est jamais accepte pour un seuil entier.

Chaque annotation doit avoir exactement la forme :
```json
{
  "schema": "openpdf.office.visual-fidelity.annotation.v558",
  "source_sha256": "64 caracteres hexadecimaux correspondant au PDF source",
  "office_sha256": "64 caracteres hexadecimaux correspondant au DOCX/XLSX/PPTX",
  "rendered_pdf_sha256": "64 caracteres hexadecimaux correspondant au PDF de rendu",
  "origin": "human_reviewed",
  "renderer": "libreoffice",
  "renderer_version": "24.2.7.2"
}
```

Les phrases descriptives ci-dessus ne sont pas des empreintes utilisables : remplacer les trois champs SHA par les SHA-256 reels. `origin` vaut `human_reviewed` ou `synthetic_known_at_generation`. La premiere valeur est une declaration de provenance, pas une signature.

## Definitions et limites des mesures

- **Erreur raster MAE** : moyenne des differences absolues des niveaux de gris, entre 0 et 255, sur les pixels des pages communes. Quand les tailles raster different, le rendu est redimensionne pour la comparaison ; l'ecart de dimensions physiques reste rapporte separement.
- **Fraction de pixels modifies** : proportion dont la difference depasse 16 niveaux de gris. Ce seuil est fixe, distinct des seuils utilisateur.
- **Precision / rappel** : comparaison multiensemble des tokens extraits du PDF source et du PDF de rendu. Les tokens sont normalises en Unicode NFKC et en minuscules.
- **Rappel d'ordre** : taille LCS exacte de la sequence des tokens, divisee par le nombre de tokens du PDF source.
- **IoU et derive** : moyenne des boites normalisees des mots apparies par sequence. Les mots non apparies n'ont pas de mesure de geometrie ; le rappel de texte et la rasterisation restent donc des controles complementaires.

Les seuils sont evaluates sur les valeurs non arrondies. Un rapport PASS signifie uniquement que les seuils choisis ont ete respectes sur les preuves donnees.

## Securite, ressources et vie privee

- Refus des chemins absolus, traversal et liens symboliques au moyen du garde de fichiers V539.
- Prevalidation du paquet OOXML reutilisee depuis V542, dont CRC, noms dangereux, relations externes, contenu actif et budgets d'expansion.
- SHA-256 des preuves avant/apres analyse et liaison des annotations aux trois artefacts.
- Budgets : 32 cas, 32 pages par PDF, 96 pages cumulees, 8 millions de pixels par page, 100 millions de pixels estimes cumules, 5 000 tokens par PDF/cas, 50 000 tokens cumules.
- Les recus n'exportent ni le texte PDF, ni le nom des fichiers, ni leur chemin. Le manifeste local contient les chemins et doit etre conserve avec les protections adaptees.
- SHA-256 assure l'integrite des octets au moment du controle, mais pas l'identite ou l'authenticite de l'editeur. Le programme n'effectue aucune analyse antivirus.

## Qualification

Les suites V558 utilisent des PDF et fichiers Office synthetiques connus au moment de leur generation. Elles couvrent les cas identiques, decalage geometrique, mots manquants/inattendus, page supplementaire, changements d'empreintes, JSON ambigus, liens symboliques, OOXML actif, PDF invalide, seuils mal formes et recus confidentiels.

La CI Ubuntu/Windows doit confirmer les tests V558. Les builds natifs Windows, l'installation/desinstallation silencieuses et le ZIP cumulatif restent des controles separes et doivent etre verifies sur le SHA exact de la branche. Aucune signature Authenticode, revue graphique humaine ou certification de fidelite d'un corpus metier n'est revendiquee.

## Livrables V558

- Moteur : `03-Sources/openpdf_office_visual_fidelity_v558.py`
- Tests : `04-Tests-et-Qualification/test_office_visual_fidelity_v558.py`
- Generateur Word/PDF et diagrammes : `02-Compilation/generate_docs_v558.py`
- Rapport Word/PDF, PNG et SVG : generes au packaging cumulatif dans `05-Documentation`
- Integrite du runtime : manifeste V51.4 et SHA-256 des sources reconciles.
