# OpenPDF Studio V25.5 — Liaison audit/PDF
Auteur : Abdelhalim Talbi

Cette version ajoute un outil **hors ligne** de liaison des preuves exportées V25.4 aux octets exacts des deux PDF. L’interface HTML n’a pas accès aux PDF originaux dans tous les modes : aucune empreinte de PDF n’est inventée dans le navigateur.

```bash
python bind_pdf_audit_v255.py bind audit-v25.4.json source.pdf cible.pdf -o audit-lie-v25.5.json
python bind_pdf_audit_v255.py verify audit-lie-v25.5.json source.pdf cible.pdf
```

Le vérificateur contrôle la chaîne SHA-256 des événements, l’empreinte de l’enveloppe, les tailles et les empreintes SHA-256 des deux PDF. Il échoue si un document a changé, si les deux PDF sont inversés ou si l’audit a été altéré. La vérification nécessite les **PDF exacts** ; les noms de fichiers ne sont pas des identifiants de sécurité.

Limites : intégrité **sans signature, authentification ni horodatage de confiance** ; un acteur pouvant modifier les trois fichiers peut recalculer toutes les empreintes. Les tests du module ne valent pas qualification native Windows.
