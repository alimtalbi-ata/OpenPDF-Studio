# OpenPDF Studio V28.7 — Guide de qualification Windows
Auteur : Abdelhalim Talbi

1. Extraire l’archive dans un répertoire local inscriptible sur Windows 10/11 x64.
2. Exécuter `BUILD-WINDOWS-INSTALLER.cmd` (réseau et droits d’installation des outils nécessaires).
3. Contrôler `build-v28.7.log`, `dist\OpenPDF-Studio\OpenPDF-Studio.exe` et `installer\OpenPDF-Studio-V28.7-Setup.exe`.
4. Lancer `QUALIFY-WINDOWS-V28.7.cmd` dans une session graphique interactive ; examiner `qualification-windows-v28.7.json` et la capture réelle si disponible.
5. Installer le Setup, ouvrir l’application via le menu Démarrer et tester fusion, extraction, compression et annulation sur des copies de documents.
6. Vérifier raccourcis, journalisation et désinstallation via Paramètres Windows.

**Limite :** les étapes 2–6 n’ont pas été exécutées dans l’environnement Linux de production de l’archive. La présence de scripts et le succès des tests Python ne constituent pas une qualification native Windows.
