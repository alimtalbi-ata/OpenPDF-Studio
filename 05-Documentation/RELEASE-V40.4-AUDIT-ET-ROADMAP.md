# OpenPDF Studio — V40.4 release audit and roadmap
Auteur : Abdelhalim Talbi

## Portée V40.4
- Interface : commandes permanentes, raccourci Ctrl+L vers destination, recentrage en cas d'erreur, noms de sortie suggérés.
- Sécurité des livrables : manifeste SHA-256 de chaque fichier de l'archive cumulative, contrôle de présence du manifeste dans le ZIP, contrôles automatisés Windows.
- Contrôles : tests unitaires et contrats d'interface en CI. Une réussite CI ne constitue pas une recette humaine de l'interface Windows.
- Limites : aucune preuve de capture réelle Windows haute résolution / DPI, aucun essai d'installation sur un poste Windows indépendant; ne pas les présenter comme réalisés.
- Documentation Word/PDF : les manuels V40.0–V40.2 restent des références historiques et ne doivent pas être considérés comme manuels V40.4 actualisés.

## Analyse d'utilité des composants
- Ajouter/retirer les PDF : indispensable à la sélection des entrées; une source hors fusion, plusieurs pour fusion.
- Opérations : compression, fusion, extraction, découpage, réorganisation, OCR et conversions Office sont les parcours prioritaires.
- Destination : critique pour éviter les erreurs et protéger les sources; ne pas masquer son accès.
- Aperçu : utile pour vérifier visuellement le PDF avant traitement, ne doit jamais bloquer l'exécution.
- Journal et progression : visibilité et diagnostic; la progression indéterminée ne représente pas un pourcentage réel.
- Récupération : nécessaire pour les transactions de découpage interrompues, ne doit pas toucher les fichiers inconnus.

## Plan prévisionnel
### V40.5 — qualification ergonomique
Tests Windows DPI 100/125/150/200 %, clavier, lecteurs d'écran, fenêtres réduites; captures réelles; guide utilisateur Word/PDF à jour.

### V40.6 — moteur de conversion
Jeux de documents de référence pour Word/Excel/PowerPoint, métriques de fidélité, tableaux complexes, OCR et limites explicites.

### V40.7 — fiabilité des sorties
Audit systématique des écritures atomiques, collisions de fichiers, transactions interrompues, simulation d'échec disque, reprise et traçabilité.

### V40.8 — installateur autonome
Qualification sur Windows propre sans sources Python, inventaire SBOM, vérification des dépendances et signatures de distribution si disponibles.
