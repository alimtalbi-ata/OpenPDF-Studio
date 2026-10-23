# OpenPDF Studio V51.3 — OCR autonome vérifié et intégrité des modèles

**Auteur : Abdelhalim Talbi** — 24 octobre 2026.

## Évolution produit

La V51.3 corrige une limite du portable Windows V51.2 : les modèles linguistiques Tesseract anglais et français n'étaient pas garantis dans les exécutables. Le compilateur Windows récupère les deux modèles officiels `tessdata_fast` pendant le build, vérifie leur taille et leur SHA-256, puis les embarque dans le portable et l'installateur. Aucun téléchargement n'est effectué lors d'une opération OCR.

Le moteur OCR résout explicitement le dossier `tessdata` du binaire PyInstaller (ou un dossier choisi par l'utilisateur) et refuse tout modèle intégré altéré, manquant ou remplacé par un lien symbolique. Il ne revient jamais silencieusement au modèle système pour un exécutable gelé.

## Chaîne d'exécution et preuves

`BUILD-OPENPDF-WINDOWS.cmd` → installation des dépendances → téléchargement et SHA-256 des modèles officiels → PyInstaller avec `tessdata` embarqué → auto-tests OCR réels → installation et OCR depuis l'application installée → désinstallation → manifestes. Les reçus CI ne sont considérés comme preuve que si les jobs Windows ont réellement réussi.

Modèle eng : 4 113 088 octets, SHA-256 `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2`.

Modèle fra : 1 130 365 octets, SHA-256 `ced037562e8c80c13122dece28dd477d399af80911a28791a66a63ac1e3445ca`.

Source officielle : https://github.com/tesseract-ocr/tessdata_fast ; licence Apache-2.0 conservée à côté des modèles dans les binaires.

## Qualification exécutée localement

12 tests du résolveur (dont test OCR réel sur PDF image synthétique), 11 tests du pipeline Office OCR et fermeture statique des modules. Le test réel reconnaît « OPENPDF OCR CHECK 12345 », vérifie une page OCR et l'empreinte du PDF. Ceci démontre la reconnaissance sur le document de test, pas l'exactitude sur un corpus métier.

## Limites et risques

Le build Windows dépend d'un accès HTTPS à GitHub pour récupérer les modèles lors de la compilation, sauf cache vérifié. Le portable n'est pas signé Authenticode. L'OCR réel du binaire Windows, la GUI Windows humaine et la fidélité Office complexe doivent être validés par CI/qualification native : aucun test Linux n'est une preuve Windows. Le logiciel ne certifie pas l'exactitude de l'OCR, PDF/A ou la fidélité Office.

## Prochaine priorité

Exécuter la CI Windows native sur V51.3, récupérer les exécutables et reçus, réaliser des tests OCR sur documents métier réels et améliorer les indicateurs de qualité et la conversion de tableaux vers Excel.
