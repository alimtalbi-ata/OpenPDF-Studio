# OpenPDF Studio V42.8 — Protection contre les modifications concurrentes
Auteur : Abdelhalim Talbi

## Problème
Lors d'une compression longue, le PDF source peut être modifié par une autre application. Le résultat peut alors correspondre à une ancienne version du fichier.

## Correctif
- Capture des métadonnées source au début de l'opération (taille, date de modification nanoseconde, identifiant de fichier).
- Nouvelle comparaison immédiatement avant publication exclusive.
- Refus et nettoyage du temporaire si une modification est détectée.
- Test de régression simulant une modification réelle du PDF pendant la compression.
- Aucun écrasement de la destination.

## Limites
Un contrôle de métadonnées ne constitue pas une preuve cryptographique d'immuabilité ; un changement avec conservation artificielle des métadonnées peut échapper à ce contrôle. La fenêtre entre vérification et publication ne peut pas être complètement supprimée sans mécanisme de verrouillage. Qualification Windows automatisée à confirmer.
