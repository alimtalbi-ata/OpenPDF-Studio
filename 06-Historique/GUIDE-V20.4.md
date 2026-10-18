# OpenPDF Studio V20.4 — Zoom et défilement synchronisé

Auteur : Abdelhalim Talbi

## Utilisation
1. Générer le diagnostic HTML avec `python diagnostic_dashboard.py rapport.json sortie.html --source-pdf source.pdf --target-pdf cible.pdf`.
2. Ouvrir `sortie.html` dans un navigateur récent.
3. Utiliser `+`, `−` et `Réinitialiser` pour régler le zoom des deux aperçus à 50, 75, 100, 125, 150, 200, 250 ou 300 %.
4. Faire défiler un volet : si **Défilement synchronisé** est coché, l'autre volet suit en proportion de sa hauteur et de sa largeur défilables.
5. Décocher l'option pour examiner séparément les documents. Les contrôles ne concernent que les comparaisons 1:1 avec deux aperçus disponibles.

## Limites
La synchronisation proportionnelle ne constitue pas un alignement sémantique des lignes. Elle ne synchronise pas les candidats 1:2 / 2:1. Les images restent des rendus PDF; aucune capture réelle de l'application Windows n'a été effectuée. Il s'agit d'un add-on de diagnostic, pas du logiciel Windows complet.
