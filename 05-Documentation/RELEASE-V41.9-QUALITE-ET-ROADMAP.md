# OpenPDF Studio V41.9 — Publication exclusive de la compression
Auteur : Abdelhalim Talbi

## Risque confirmé dans le code
Le moteur de compression utilisait os.replace(temporaire, destination), qui écrase silencieusement un fichier apparu pendant la compression. La validation préalable ne protège pas contre cette condition de concurrence.

## Correctif
- Publication de compression via publish_exclusive, mécanisme commun aux autres services PDF.
- Refus d'écraser un document apparu entre validation et publication.
- Conservation du fichier tiers et nettoyage du fichier temporaire.
- Test de régression reproduisant la concurrence avec un PDF source réel.

## Critères de qualité
P1 : intégrité des fichiers utilisateur et absence d'écrasement involontaire. P1 : validation des opérations PDF principales. P2 : fidélité Office/OCR et recette visuelle Windows. L'interface reste Tkinter tant que sa migration n'apporte pas un bénéfice mesurable et démontré.

## Qualification
Tests et compilation Windows via GitHub Actions. Aucune capture réelle d'interface n'est fournie par ce changement ; aucune capture fictive n'est revendiquée.
