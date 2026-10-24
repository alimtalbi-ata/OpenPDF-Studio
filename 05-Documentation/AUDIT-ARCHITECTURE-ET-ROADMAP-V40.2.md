# OpenPDF Studio — Audit technique et feuille de route (base V40.2)

Auteur : Abdelhalim Talbi  
Statut : audit statique ciblé, branche `develop/v40.5-windows-ci`. Les constats de code ne remplacent pas une recette Windows propre.

## 1. Périmètre et inventaire observé
Inventaire GitHub au 18 octobre 2026 : **1 093 fichiers** dont **625 dans 03-Sources**, **103 dans 04-Tests-et-Qualification**, **46 dans 05-Documentation**, **287 dans 06-Historique** et **9 dans 07-Manifestes**. Dans 03-Sources : **570 fichiers Python** ; **564 fichiers du répertoire ont un identifiant de version dans le nom**. Ce comptage ne démontre pas qu'ils sont tous chargés à l'exécution. La forte accumulation de variantes appelle une cartographie des imports et une politique d'archivage.

Fichiers effectivement examinés : `openpdf_studio.py`, `openpdf_desktop.py`, `openpdf_operations.py`, `openpdf_page_service_v345.py`, `openpdf_compression_service_v344.py`, `openpdf_conversion_service_v351.py`, `openpdf_ocr_service_v347.py`, `openpdf_publish_binary.py`, `openpdf_binary_manifest.py`, ainsi que la chaîne de compilation/qualification Windows. **Ne pas interpréter cet échantillon comme un audit ligne par ligne des 1 093 fichiers.**

## 2. Architecture réelle observée
```text
openpdf_studio.py (entrée / self-tests)
  -> openpdf_desktop.py (Tkinter, navigation, file de tâches)
    -> openpdf_operations.py (validation, réservation, récupération split)
      -> openpdf_ui_controller_v348.py (dispatch historique)
        -> services et contrôleurs hérités, selon opération
  -> openpdf_functional_smoke.py (autotest)
BUILD-WINDOWS-INSTALLER.cmd
  -> PyInstaller onedir -> smoke -> Inno Setup -> test installation
  -> PyInstaller onefile -> smoke -> preuves SHA256
  -> openpdf_release_gate.py -> openpdf_publish_binary.py
  -> openpdf_binary_manifest.py -> VERIFY-WINDOWS-RELEASE.ps1
```
Le dispatch de production repose encore sur un contrôleur suffixé `v348` : éviter de remplacer brutalement les modules historiques sans prouver leur couverture fonctionnelle.

## 3. Constats classés par priorité
| Priorité | Constat vérifiable | Risque / action |
|---|---|---|
| P0 | `openpdf_conversion_service_v351.py` utilisait `os.fsync` sur un fichier ouvert `rb`. | Échec possible sous Windows ; corrigé sur la branche de travail en ouvrant `r+b`. Ajouter un test Windows de conversion Office réelle. |
| P0 | `openpdf_page_service_v345.py` valide la cible mais `_publish` utilise `os.replace` sans interdiction d'écraser un fichier existant. | Écrasement silencieux possible ; publication exclusive et tests de concurrence à mettre en place avant branchement généralisé. |
| P0 | Les contrôles PE, self-tests et SHA256 ne constituent pas une preuve d'exécution sur un PC vierge. | Tester installateur + portable sur une VM Windows sans Python/Tesseract/LibreOffice ; matrice de dépendances. |
| P1 | `openpdf_desktop.py` affiche toujours « V38.5 » alors que `VERSION.txt` indique V40.2. | Version UI incohérente ; lire une unique source de version au runtime et dans les métadonnées. |
| P1 | Le dispatch public `openpdf_operations.py` dépend de `openpdf_ui_controller_v348.py`. | Couplage et dette de versions ; façade stable `core/operations.py` et adaptateurs progressifs. |
| P1 | Les services de publication emploient plusieurs stratégies : `os.replace`, `os.link`, transaction dédiée, réservation. | Sémantique divergente, particulièrement sur Windows/SMB ; centraliser politique no-overwrite, fsync, rollback, reçus. |
| P1 | L'OCR exige Tesseract local et les données de langue ; conversion Office a des dépendances variables. | L'EXE ne suffit pas à garantir ces fonctions ; détecter, afficher et documenter les capacités réellement disponibles. |
| P1 | 564 fichiers de 03-Sources portent un suffixe de version. | Maintenance et taille d'audit difficiles ; classifier actif/historique/compatibilité avant toute suppression. |
| P2 | `03-Sources/README.md` annonce V26.7 et un ancien script. | Documentation contradictoire ; pointer vers une page de référence maintenue. |
| P2 | Compression `smaller_only` distingue un résultat sans gain d'une sortie publiée. | Bonne sémantique à conserver et exposer clairement dans l'interface. |

## 4. Priorisation produit (usage avant sophistication)
1. **Fusionner / découper / extraire / réorganiser** : sélection de fichiers, aperçu, glisser-déposer, progression, annulation sûre, résultat vérifié.
2. **Compresser** : taille avant/après, estimation du gain, profils lisibles, aucune dégradation silencieuse et pas de fausse « réussite » sans gain.
3. **Conversion PDF → Word / Excel / PowerPoint** : expliciter la fidélité et les limites, fournir aperçu/rapport de qualité, préserver tableaux et mises en page lorsque possible. Ne pas promettre une conversion 100 % éditable.
4. **OCR hors ligne** : langues FR/EN, détection du moteur, barre de progression, choix pages scannées uniquement, validation du PDF consultable.
5. **Traitement par lots** : file d'attente, reprise, rapports et journal exploitable.
6. Fonctions avancées ensuite : annotations, formulaires, signatures cryptographiques, comparaison visuelle, caviardage vérifié.

## 5. Cible de rationalisation sans rupture
```text
03-Sources/
  openpdf_studio.py             # entrée stable conservée
  openpdf/                      # futur package (migration progressive)
    app/                        # UI, navigation, préférences
    core/                       # modèles, erreurs, validation, reçus
    services/                   # pages, compression, conversion, OCR
    infrastructure/             # publication, verrous, journal, capacités
    adapters/                   # modules vNNN hérités
  legacy/                       # uniquement modules prouvés non actifs ou adaptateurs
02-Compilation/                 # unique point d'entrée Windows
04-Tests-et-Qualification/      # unitaires, intégration, fixtures, Windows VM
05-Documentation/               # architecture, utilisateur, installation, build, API, qualité
06-Historique/                  # archives et anciennes versions
07-Manifestes/                 # SBOM, versions, empreintes, provenance
```
**Règle :** ne déplacer aucun module avant extraction d'un graphe d'imports statiques + imports dynamiques, identification des points d'entrée, tests de non-régression et vérification PyInstaller `hiddenimports`.

## 6. Plan de livraison
### V40.3 — Stabilisation P0
- Publication sans écrasement pour toutes les opérations, y compris les cibles créées en concurrence.
- Tests Windows pour fsync, fichiers verrouillés, chemins Unicode/espaces, fichiers existants, interruption et rollback.
- Version unique UI / CLI / manifeste / installeur ; diagnostics de dépendances.
- Deux vrais EXE + manifeste SHA256 + rapports de smoke et installation. Critère de sortie : workflow vert **et** essai VM Windows propre.

### V40.4 — UX et fonctions essentielles
- Écran d'accueil à actions principales, sélecteur de documents, paramètres contextuels, destination prévisible.
- Aperçu multipage avec cache borné ; progression et annulation ; résultats avant/après.
- Qualification sur corpus PDF : texte, scan, images, tableaux, volumineux, chiffré, corrompu.

### V40.5 — Architecture modulaire
- Façade `core` stable, adaptateurs `legacy`, séparation UI/services.
- Tests contractuels identiques pour ancien et nouveau dispatch.
- Cartographie des imports et nettoyage contrôlé, sans suppression massive.
- Pipeline CI unitaires + intégration + Windows ; documentation Word/PDF cumulative.

### V40.6 — Qualité Office et OCR
- Bench de fidélité DOCX/XLSX/PPTX (structure, texte, images, tableaux, lisibilité).
- Capacités optionnelles clairement détectées ; pack OCR hors ligne documenté et testé.
- Traitement par lots fiable, suivi des tâches et export des rapports.

### V41.0 — Produit Windows prêt à distribuer
- Installateur silencieux/désinstallation, portable sans écriture non voulue dans le système, signatures si certificat disponible.
- SBOM et licences des composants ; antivirus faux positifs, SmartScreen et politique de mises à jour.
- Recette Windows 10/11 propre, utilisateur standard, hors ligne ; vérification EXE sans sources.
- Documentation Word/PDF, captures **réelles** et limites explicites, intégrées au ZIP cumulatif.

## 7. Indicateurs et critères de validation
- Taux de réussite par opération et corpus ; zéro écrasement involontaire ; zéro sortie partielle déclarée « réussie ».
- Taux de succès installation et démarrage sur VM Windows vierge ; couverture FR/EN OCR.
- Temps, mémoire et taille de sortie sur corpus reproductible ; pas de régression au-delà d'un seuil documenté.
- Nombre de modules effectivement chargés, dépendances directes, chemins legacy restants, couverture tests.
- Empreinte SHA256, provenance du runner, versions exactes des dépendances, rapport de qualité par artefact.

## 8. Politique de changement
Préserver `main` ; travailler dans `develop/v40.5-windows-ci` et PR #1. Chaque refonte doit être incrémentale, réversible, testée. Aucun binaire ne doit être annoncé comme disponible sans artefact GitHub ou fichier réellement vérifié.
