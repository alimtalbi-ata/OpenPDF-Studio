# OpenPDF Studio V26.5 — Guide Windows

Auteur : Abdelhalim Talbi.

## Démarrage
1. Installer Python 3.9+ sur Windows et cocher « Add Python to PATH ».
2. Dans le dossier extrait : `py -3 -m pip install -r requirements-windows-v260.txt`.
3. Double-cliquer `LANCER-OPENPDF-STUDIO.cmd`.
4. Ajouter un PDF, le sélectionner et cliquer « Aperçu / pages » ou double-cliquer le document.
5. Dans l’onglet **Éditeur de pages**, sélectionner les pages, déplacer, tourner, supprimer et enregistrer sous un nouveau PDF.
6. Dans l’onglet **Propriétés du PDF**, consulter les informations du document.

## Limitations
Le panneau des opérations historiques reste visible au-dessus des nouveaux onglets : la migration vers une barre d’outils compacte n’est pas achevée. L’aperçu est synchrone et peut ralentir l’UI pour de gros PDF. Les tests ont lieu sous Linux, pas encore sous Windows natif. Les captures réelles Windows et un .exe précompilé ne sont pas disponibles.
