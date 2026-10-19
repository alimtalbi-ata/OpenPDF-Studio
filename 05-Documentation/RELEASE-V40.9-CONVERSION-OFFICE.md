# OpenPDF Studio V40.9 — Conversion Office : recette fonctionnelle
Auteur : Abdelhalim Talbi

## Tests réels
Les tests génèrent un PDF de deux pages avec des marqueurs textuels distincts, invoquent le moteur réel de conversion et ouvrent les documents Word, Excel et PowerPoint obtenus à l'aide de leurs bibliothèques natives.

- DOCX : présence des marqueurs éditables, SHA-256 du reçu.
- XLSX : présence des marqueurs dans les cellules, ouverture effective du classeur.
- PPTX : deux diapositives, marqueur correct sur chaque diapositive.
- Destination existante : refus d'écrasement et octets préservés.

## Ce que ces tests ne prouvent pas
La fidélité visuelle n'est pas mesurée. La conversion est essentiellement textuelle; les tableaux, polices, images, formulaires et objets complexes ne sont pas restitués à l'identique. La CI n'est pas un test manuel de l'interface.

## Suite prévue
V41.0 : mesures de fidélité et avertissements dans l'interface, documentation Word/PDF spécifique à la version, audit JSON des opérations et tests d'installation Windows.
