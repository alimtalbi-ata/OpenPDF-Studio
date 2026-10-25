# OpenPDF Studio V41.1 — Garantie documentaire et archive vérifiable
Auteur : Abdelhalim Talbi

## Modification de fiabilité
La construction de l'archive cumulative échoue si le guide DOCX ou PDF correspondant exactement à VERSION.txt manque, est vide ou n'est pas intégré dans le ZIP. Cette vérification s'applique avant la publication de l'artefact Windows.

## Vérifications
- Deux fichiers obligatoires : OpenPDF-Studio-V41.1-Guide.docx et OpenPDF-Studio-V41.1-Guide.pdf.
- Taille minimale de chaque document : 1 000 octets.
- Présence obligatoire de chacun dans le ZIP final.
- Inventaire SHA-256 de tous les fichiers embarqués, y compris ces documents.
- Maintien des sources, exécutables, scripts de build et qualification dans l'archive unique.

## Limites et suite
Ces contrôles garantissent la présence, pas la profondeur éditoriale ni la qualité visuelle des guides. Les captures réelles d'interface ne sont pas produites par la CI. Prochaine étape : améliorer la documentation par captures de fenêtres Windows automatisées et qualifier les sorties Office complexes.
