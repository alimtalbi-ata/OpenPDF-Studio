# OpenPDF Studio V25.7 — Assistant graphique d’audit
Auteur : Abdelhalim Talbi

## Windows (prioritaire)
Installer Python 3 avec Tcl/Tk, puis lancer `python audit_assistant_v257.py` depuis le répertoire de l’application. Deux onglets : **Constituer un dossier** (journal JSON, PDF source, PDF cible, sortie ZIP) et **Vérifier un dossier** (ZIP autonome). Le rapport est affiché dans l’interface. Aucun envoi réseau.

## Sécurité et limites
L’assistant contrôle les chemins avant traitement, demande confirmation avant écrasement et crée le ZIP dans un fichier temporaire avant publication après vérification. Il ne remplace pas une signature numérique, un horodatage qualifié ni une preuve d’identité. Les PDF originaux sont contenus dans le ZIP. Ne pas diffuser sans contrôle d’accès.

## Recette
Tests de logique GUI automatisés sans écran. Une capture native Windows n’a pas été réalisée. Voir `CAPTURES-STATUS.md`. La version actuelle est un assistant du module de diagnostic, pas un éditeur PDF Windows complet.
