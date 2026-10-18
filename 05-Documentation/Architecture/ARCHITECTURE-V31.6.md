# Architecture OpenPDF Studio V31.6

Auteur : Abdelhalim Talbi

```mermaid
flowchart TD
 A[Interface Tkinter v316] --> B[Interface héritée v315]
 B --> C[Parcours guidés v313 à v315]
 C --> D[Contrôles de saisie et validation]
 D --> E[Contrôleur asynchrone v309]
 E --> F[Moteur PDF v272 et convertisseurs]
 F --> G[Fichier de sortie]
 E --> H[État de progression et erreurs]
```

L'interface V31.6 hérite de V31.5. Aucun nouveau moteur PDF n'est introduit. Les contrôles sur la sortie et la prévention de remplacement de source sont assurés dans les parcours guidés existants.

## Organigramme d'utilisation

```mermaid
flowchart TD
 A[Choisir une action] --> B[Ajouter les fichiers]
 B --> C[Configurer ordre ou options]
 C --> D{Validation OK ?}
 D -- Non --> B
 D -- Oui --> E[Choisir destination]
 E --> F{Destination existante ?}
 F -- Oui --> G[Demander confirmation]
 G --> H[Lancer traitement]
 F -- Non --> H
 H --> I[Résultat ou erreur]
```
