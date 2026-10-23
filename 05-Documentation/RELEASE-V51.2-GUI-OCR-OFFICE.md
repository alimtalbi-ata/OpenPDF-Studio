# OpenPDF Studio V51.2 — OCR Office depuis l'interface

**Auteur : Abdelhalim Talbi.** Statut : code source candidat, pas de qualification Windows V51.2 avant CI.

## Fonctionnalité

Les opérations **Vers Word**, **Vers Excel** et **Vers PowerPoint** proposent la langue OCR et une case **OCR avant conversion**. La case est décochée par défaut. Si activée, le dispatcher appelle le pipeline hors ligne V51.1 avec la même réservation de destination et le même audit que les autres opérations. Sinon, le chemin historique de conversion est conservé.

Le résultat Office contient du texte éditable, sans garantie de reconstruction fidèle de la mise en page, des tableaux ou des images. Les modèles linguistiques Tesseract doivent être disponibles localement ; une absence bloque la publication.

## Contrôles

- Refus des liens symboliques source pour l'OCR Office et des destinations symboliques (même cassées), refus des destinations existantes et des conversions Office multi-sources.
- Dix tests du dispatcher et du contrat d'interface réussis localement sous Linux. Ils utilisent des doubles contrôlés pour le moteur OCR : **ce n'est ni un test OCR réel ni une preuve de GUI Windows**.
- Tests réels OCR→Office V51.1 maintenus en régression séparée.
- Fermeture statique versionnée V51.2, 92 modules requis. Point d'entrée build Windows inchangé : `02-Compilation/BUILD-WINDOWS-INSTALLER.cmd`.
- Aucun binaire V51.2, screenshot Windows, test d'installation ou signature Authenticode ne doit être annoncé sans preuve d'exécution.

## Prochaine priorité

Exécuter les CI Linux/Windows, produire les binaires V51.2, tester l'OCR depuis le portable autonome avec les langues eng/fra, puis qualifier le parcours graphique réel et mesurer la fidélité des sorties.
