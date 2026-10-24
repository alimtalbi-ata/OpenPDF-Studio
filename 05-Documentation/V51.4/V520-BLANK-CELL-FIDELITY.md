# OpenPDF Studio V520 - Fidélité des cellules vides PDF vers Excel

**Auteur : Abdelhalim Talbi**  
**Application : V51.4** - évolution ciblée de l'évaluateur de fidélité (QA Python).

## Défaut corrigé

L'oracle indépendant V517 comptait les cellules non vides supplémentaires *hors* de la grille annotée, mais ignorait les valeurs inventées *dans* une cellule que l'annotation déclarait vide. Le gate de corpus V519 pouvait ainsi rendre PASS lorsque l'exactitude des cellules non vides était de 100 % et le seuil `max_extra_nonempty_cells` fixé à zéro.

## Correction

Pour chaque cellule d'un tableau annoté, si la référence est vide (`None` ou chaîne vide) et si le classeur contient une valeur, l'oracle incrémente `extra_nonempty_cells`. Les compteurs existants `exact_cells`, `exact_nonempty_cells`, les mesures de fusion et la politique de sécurité restent inchangés.

Diagramme de décision :

```text
PDF + XLSX + annotations indépendantes
              |
      Vérifier sécurité OOXML
              |
      Parcourir chaque cellule
              |
      Référence vide ? --non--> Comparer exactitude
              |
             oui
              |
      XLSX contient valeur ?
          |          |
         oui        non
          |          |
   +1 extra cell  aucune erreur
          \          /
           Agrégation V519
                |
      Seuil extra dépassé ?
          |          |
         oui        non
          |          |
        FAIL     Autres seuils
```

## Qualification locale réalisée

- 4/4 nouveaux tests fonctionnels PASS sous Linux, avec deux PDF synthétiques réellement convertis en XLSX.
- 84/84 tests de régression `test_xlsx*.py` PASS sous Linux.
- Contrôle positif : tableau correct, cellule vide conservée.
- Contrôle négatif : valeur inventée en C4 ou C5, détectée et rejetée par le gate.
- Non-régression : valeur supplémentaire hors grille encore détectée.
- Aucun texte de cellule injecté n'est présent dans les rapports JSON.

## Limites

Les annotations sont synthétiques, connues lors de la génération du PDF, et **non** validées par un humain. Aucun test de fidélité visuelle, aucune interaction GUI Windows humaine et aucun nouveau binaire Windows ne sont revendiqués dans cette note. La CI Ubuntu/Windows doit confirmer les tests après push. Les exécutables V51.4 précédents ne contiennent pas ce correctif d'outil QA.

## Prochaine priorité

Constituer un corpus PDF métier annoté humainement, couvrant tableaux sans bordures, scans, cellules fusionnées et tableaux multipages ; ensuite exiger une qualification Windows native des nouveaux livrables.
