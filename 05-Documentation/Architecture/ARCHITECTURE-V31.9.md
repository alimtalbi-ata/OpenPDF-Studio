# ARCHITECTURE-V31.9.md

Interface Tkinter (openpdf_windows_v319) → parcours guidé (openpdf_compression_v319 / openpdf_guided_v315) → ordonnanceur asynchrone (openpdf_windows_v272) → moteur PyMuPDF (openpdf_engine_v272) → écriture atomique (openpdf_engine_v271) → PDF de sortie. Les conversions utilisent des modules distincts.

Accueil → Compresser → Choix source → Vérification PDF → Choix destination → Contrôle anti-écrasement → Confirmation si destination existante → Exécution asynchrone → Résultat / erreur. Annulation de sélection → retour accueil.
