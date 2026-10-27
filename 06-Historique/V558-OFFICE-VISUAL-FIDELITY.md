# Historique - V558 PDF / Office visual fidelity

Date de developpement : 27 octobre 2026.
Auteur : Abdelhalim Talbi.

## Modification

Ajout d'un controle de fidelite visuelle et geometrique entre PDF source et PDF de rendu d'un candidat DOCX/XLSX/PPTX. Le moteur verifie :
- les nombres de pages et leurs dimensions ;
- l'erreur raster en niveaux de gris et la fraction de pixels modifies ;
- la precision, le rappel et l'ordre d'extraction des tokens ;
- l'IoU et la derive moyenne des boites de mots ;
- les empreintes SHA-256 et la stabilite des preuves, la prevalidation OOXML, les budgets et les chemins sans liens symboliques.

Le controle est accessible dans la GUI par un dialogue asynchrone et peut exporter un recu JSON agrege sans texte ni chemins. La documentation Word/PDF et les diagrammes sont produits par le generateur V558 pendant le packaging ; les diagrammes sont clairement identifies comme schemas et non comme captures UI.

## Preuves et conditions

Les tests V558 ont des fixtures synthetiques. Ils ne sont pas des preuves de conversion sur un corpus metier. Le moteur de rendu indique par l'annotation est une provenance declaree, non attestee. La geometrie des mots depend de l'extraction PDF ; elle ne remplace pas une revue humaine. Le raster depend du moteur PDF et de la resolution.

La qualification release exige la CI Ubuntu/Windows sur le SHA exact, source closure, construction native Windows, smoke portable, installateur, installation/desinstallation et ZIP cumulatif verifie (CRC, inventaire et SHA-256). Aucune etape n'est declaree reussie avant observation. Aucun merge automatique ; `main` est preservee.

