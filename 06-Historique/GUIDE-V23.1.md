# OpenPDF Studio V23.1 — Qualification fonctionnelle en navigateur
Auteur : Abdelhalim Talbi

## Nouveautés
- Correction d'une erreur d'exécution JavaScript : la collection `rows` était utilisée avant son initialisation.
- Script reproductible `python browser_qualification_v231.py` utilisant Playwright et Chromium.
- Qualification des contrôles de filtre et de réinitialisation, et surveillance des erreurs JavaScript.
- Capture réelle Linux/Chromium dans `captures-v23.1/dashboard-chromium-real.png`.
- Résultats machine lisibles dans `captures-v23.1/browser-qualification.json`.

## Reproduire
Installer Playwright et Chromium ; lancer `python browser_qualification_v231.py` depuis le dossier de l'add-on. Le navigateur est exécuté en mode headless et le contenu du rapport est chargé directement, sans accès réseau.

## Limites
Le rapport testé est un rapport vide généré par `build_dashboard({})` : les scénarios avec documents PDF réels, les téléchargements d'exports, l'accessibilité complète et la qualification native Windows restent à couvrir. Les captures du navigateur Linux ne doivent pas être présentées comme des captures Windows. Cette archive est un add-on de diagnostic, pas l'application Windows complète.
