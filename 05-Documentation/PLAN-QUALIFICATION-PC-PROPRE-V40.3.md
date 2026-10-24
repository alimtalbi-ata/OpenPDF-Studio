# OpenPDF Studio V40.3 — Recette Windows indépendante

Auteur : Abdelhalim Talbi

Statut : plan de recette, non exécuté sur un PC externe. Les tests GitHub Actions ne démontrent pas la compatibilité d'un PC vierge.

## Préparation
Windows 10/11 x64 sans Python ni sources. Vérifier les empreintes SHA-256 des deux EXE contre le manifeste. Utiliser des documents PDF de test non confidentiels.

## Matrice d'acceptation

| ID | Scénario | Critère attendu |
|---|---|---|
| WIN-01 | Lancement portable sans Python | Interface visible, version V40.3 |
| WIN-02 | Installation puis désinstallation | Fonctionnement et retrait corrects |
| PDF-01 | Fusion et découpage | Pages correctes, sources intactes |
| PDF-02 | Extraction et réorganisation | Ordre correct, aucune sortie écrasée |
| PDF-03 | Compression | Gain mesuré ou absence de gain explicitée |
| PDF-04 | Conversion Office | Fichier ouvrable, fidélité évaluée |
| OCR-01 | OCR sans Tesseract | Erreur compréhensible |
| OCR-02 | OCR avec Tesseract FR/EN | PDF recherchable |
| SEC-01 | Destination existante | Refus sans modification |
| UX-01 | Aperçu et navigation | Interface réactive |

## Preuves
Pour chaque cas conserver machine, date, résultat PASS/FAIL/BLOCKED, journal, SHA-256 et capture réelle. Ne jamais présenter une simulation comme une capture réelle.

## Critère de sortie
La recette indépendante n'est acquise qu'après exécution réelle de WIN-01 et WIN-02 sur un PC externe. Les fonctions OCR et certaines conversions peuvent nécessiter des dépendances additionnelles.
