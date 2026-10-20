# OpenPDF Studio V43.0 — Fusion PDF et protection des sources
Auteur : Abdelhalim Talbi

## Priorité fonctionnelle
La fusion de PDF est une fonction principale. Lorsqu'un fichier source change pendant une fusion longue, la sortie risque de ne pas correspondre aux documents sélectionnés.

## Implémentation
- Capture de l'identité des sources avant la fusion (taille, date de modification nanoseconde, identifiant).
- Contrôle juste avant publication atomique du PDF fusionné.
- Refus et suppression du temporaire si une source a changé.
- Extension optionnelle du pipeline _publish avec pre_publish, sans changer les appels existants d'extraction/réorganisation.
- Tests : fusion réelle de deux PDF, modification concurrente détectée, absence de sortie partielle.

## Limites
Métadonnées et vérification finale ne constituent pas un verrouillage exclusif ni une preuve cryptographique. Les tests CI Windows ne remplacent pas des tests GUI manuels.
