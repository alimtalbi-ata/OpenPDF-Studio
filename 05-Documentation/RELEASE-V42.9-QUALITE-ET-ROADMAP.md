# OpenPDF Studio V42.9 — Cohérence source et optimisation sans gain
Auteur : Abdelhalim Talbi

## Diagnostic
L'optimisation V42.7 abandonnait rapidement un candidat plus gros que l'original. La protection V42.8 contre les modifications concurrentes n'était exécutée que pour les candidats publiables. Un PDF source modifié pendant la compression pouvait ainsi être déclaré « aucun gain » à tort.

## Correctif
- Vérification des métadonnées source sur le chemin sans gain, avant le retour.
- Si le fichier a changé, erreur explicite et nettoyage du temporaire.
- Le chemin rapide conserve son avantage : aucun contrôle raster/texte/images complet lorsque le candidat est abandonné.
- Deux tests de régression : modification concurrente détectée et chemin rapide stable.

## Limites
La détection par métadonnées n'est pas une garantie cryptographique. La qualification Windows automatisée et les contrôles GUI sont distincts.
