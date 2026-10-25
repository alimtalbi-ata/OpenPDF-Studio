# OpenPDF Studio V42.2 — Contrôle des images en compression sans perte
Auteur : Abdelhalim Talbi

## Diagnostic
Le contrôle qualité de compression vérifiait les pages et le texte, mais ne comparait pas les pixels des images incorporées.

## Développement
- Empreintes SHA-256 sur les pixels décodés des images, avec dimensions et canaux.
- Comparaison multiensemble avant/après pour les profils standard et smaller_only.
- Rejet avant publication si une image incorporée a changé.
- Profil images_balanced avec perte volontairement exclu.
- Tests PDF réels avec image conservée et image altérée.

## Limites
Le contrôle couvre les images incorporées énumérées par PyMuPDF, pas l'identité visuelle totale (masques, transparences, annotations, rendu vectoriel, ICC). La recette visuelle Windows et les captures réelles restent nécessaires. Ne pas présenter les tests CI comme une preuve exhaustive de qualité graphique.
