# OpenPDF Studio V23.4 — Audit de séquence multipage
Auteur : Abdelhalim Talbi

Le module `page_sequence_audit_v234.py` compare les pages de deux PDF par texte extrait, normalisé et haché SHA-256. Il identifie les pages identiques en texte, leurs déplacements, les pages non appariées et les différences de dimensions. Les pages blanches ne sont pas appariées automatiquement.

Exemple :
```python
from page_sequence_audit_v234 import audit_page_sequence
result = audit_page_sequence('source.pdf','cible.pdf')
```

Pour ajouter ces résultats au tableau de bord, placer le résultat dans la clé `page_sequence_audit_v234` du rapport transmis à `build_dashboard`. Les anomalies d'insertion/suppression restent qualifiées de « non appariées » ; l'identité du texte ne garantit ni la mise en page ni l'identité visuelle. Limite de 500 pages et 20 000 caractères extraits par page.

Recette : `python -m unittest discover -p 'test_*.py'`. Les captures Chromium héritées des versions précédentes ne constituent pas une nouvelle capture V23.4. Windows natif non qualifié.
