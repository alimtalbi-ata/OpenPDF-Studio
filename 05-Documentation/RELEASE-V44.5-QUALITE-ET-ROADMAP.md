# OpenPDF Studio V44.5 — Qualification fonctionnelle réelle
Auteur : Abdelhalim Talbi

## Constat d'architecture
Les versions précédentes ont principalement qualifié la compilation, les contrôles de fichiers et des scénarios simulés. Cela ne suffit pas à démontrer le fonctionnement métier.

Le code réel des conversions (openpdf_core_v260.py) extrait uniquement le texte : DOCX en paragraphes, XLSX en colonnes Page/Ligne/Texte et PPTX en zones de texte. Il ne reconstitue ni les tableaux Office natifs, ni les images, ni la mise en page d'origine. Cette limitation doit être annoncée explicitement.

## Nouveau gate de test
Un PDF est généré avec PyMuPDF. Le dispatcher public openpdf_operations.run_operation est appelé sans mocks pour :
- convertir en DOCX et relire le texte via python-docx ;
- convertir en XLSX et relire les cellules via openpyxl ;
- convertir en PPTX et relire les zones de texte via python-pptx ;
- fusionner deux PDF puis extraire une page et vérifier son contenu.

La CI Windows échouera si un de ces parcours fonctionnels échoue. Ces tests n'évaluent pas la fidélité visuelle, les PDF scannés, l'OCR ni les interactions graphiques; la recette manuelle reste obligatoire avant toute déclaration de conformité utilisateur.

## Plan prioritaire
1. Reproduire les erreurs remontées sur une machine Windows avec les PDF concernés.
2. Mettre en place un jeu de documents de référence (texte, tableaux, images, scans, PDF protégés).
3. Qualifier les résultats par format et corriger les fonctionnalités réelles avant toute cosmétique.
