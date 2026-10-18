# Audit technique V33.2
Audit statique réalisé sur les sources V33.1. Aucune recette GUI Windows n’a été effectuée.

# Chaîne des composants
UI Tkinter -> _run_pdf -> gestionnaire asynchrone -> worker PDF -> future -> _poll_v274 -> validation sortie -> bilan.

# Anomalie 1 : exceptions Future
V33.1 appelait future.result() sans garde. V33.2 intercepte les exceptions et remet l’état visuel en erreur.

# Anomalie 2 : annulation
V33.1 ne traitait pas explicitement CANCELLED. V33.2 quitte sans afficher un faux succès.

# Anomalie 3 : bilan trompeur
V33.1 vérifiait seulement is_file(). V33.2 vérifie source, destination, taille non nulle et chemins distincts.

# Anomalie 4 : lisibilité
Le bilan V33.0 utilisait une étiquette fixe de 560×320. V33.2 propose une fenêtre redimensionnable, zone texte et copie.

# Limites et risques restants
Les modules historiques sont hérités en chaîne; une refonte par composition réduirait le couplage. Les tâches parallèles restent à qualifier. Le test de sortie ne vérifie pas la structure PDF, déjà couverte partiellement par le moteur amont.

# Organigramme
[Lancer] -> [Worker] -> {Terminé ?} -> {Succès/Échec/Annulé} -> [Vérifier la sortie] -> [Afficher le bilan].

# Scénario fictif — compression
SIMULATION UNIQUEMENT : original 20 Mo, résultat 12 Mo, réduction 40 %. Ceci n’est pas une mesure issue d’un test.

# Commande CLI réelle
python -m unittest -v test_openpdf_v332.py

# Résultat attendu (illustratif)
Ran 4 tests ... OK (durée variable).

# API Python réelle
from openpdf_quality_dashboard_v332 import validate_output
rapport = validate_output("original.pdf", "sortie.pdf")

# Qualification Windows
Lancer BUILD-WINDOWS-INSTALLER.cmd sous Windows, vérifier PyInstaller/Inno Setup, tester annulation, échec, succès et copie du bilan.

# Captures
Aucune capture réelle Windows V33.2 disponible. Les schémas sont des illustrations conceptuelles et non des captures.

# Auteur
Abdelhalim Talbi