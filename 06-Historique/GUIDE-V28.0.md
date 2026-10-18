# OpenPDF Studio V28.0 — Guide Windows
Auteur : Abdelhalim Talbi

## Utilisation
Ouvrir un PDF avec **Ajouter**, puis choisir Fusionner, Compresser ou Découper. Choisir le fichier de sortie dans la boîte de dialogue. Le traitement affiche une progression et peut être annulé de façon coopérative.

## Compilation sur Windows 10/11 x64
Extraire entièrement le ZIP, puis exécuter `BUILD-WINDOWS-INSTALLER.cmd`. Le script installe les dépendances de compilation via Python/pip et, si disponible, winget/Inno Setup. Il exécute les tests puis tente de produire `installer/OpenPDF-Studio-V28.0-Setup.exe`. Connexion Internet et droits d'installation peuvent être nécessaires. Consulter `build-v28.0.log` en cas d'échec.

## Limites
Les conversions éditables et la fidélité des mises en page doivent être validées selon le type de document. L'annulation est coopérative. La compilation et l'installation Windows ne sont pas vérifiées dans l'environnement Linux utilisé pour préparer cette archive.
