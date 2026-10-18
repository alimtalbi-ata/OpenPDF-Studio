# OpenPDF Studio V25.8 — Démarrage Windows simplifié
Auteur : Abdelhalim Talbi

## Démarrer sous Windows
Décompresser **toute** l’archive dans un dossier accessible en écriture. Double-cliquer sur `LANCER-OPENPDF-AUDIT.cmd`. Le lanceur détecte Python 3.9+ (`py -3` puis `python`), vérifie les modules nécessaires et lance `audit_assistant_v257.py` uniquement si les prérequis sont satisfaits. Installer Python avec Tcl/Tk si nécessaire. Aucun téléchargement ni installation automatique.

## Vérifier les prérequis
`py -3 windows_preflight_v258.py --json` génère un bilan lisible par machine. `gui_runtime_tested=false` signifie que le contrôle ne valide **pas** l’ouverture de la fenêtre. Le lanceur est prévu pour Windows, mais son fonctionnement n’a pas été testé nativement sur Windows dans cette livraison.

## Utiliser l’assistant
Onglet **Constituer** : choisir journal d’audit JSON, PDF source, PDF cible, archive ZIP de sortie, puis lancer la création et la vérification. Onglet **Vérifier** : choisir une archive et lancer son contrôle. Le ZIP contient les documents originaux : le protéger comme les PDF.

## Périmètre
Module de diagnostic et de constitution de dossiers de preuves, pas un éditeur PDF complet. SHA-256 vérifie l’intégrité, pas l’identité de l’auteur. Les captures historiques Linux Chromium sont conservées ; aucune capture native Windows n’a été réalisée. Voir `CAPTURES-STATUS.md`.
