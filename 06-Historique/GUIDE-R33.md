# R33 — Navigation vers les pages PDF

Auteur : Abdelhalim Talbi.

Depuis un JSON produit par `compare_documents()`, générer un tableau de bord :

```bash
python diagnostic_dashboard.py diagnostic.json rapport.html --source-pdf original.pdf --target-pdf rendu.pdf
```

Les aperçus sont de **véritables rendus des pages PDF** via PyMuPDF, intégrés en base64 dans le HTML hors ligne. Seules les pages citées dans les anomalies sont rendues, au maximum 24 par côté. Les liens ne sont créés que si un aperçu existe. Le rendu Office en PDF doit être fourni séparément ; l'outil ne conserve pas les PDF temporaires de LibreOffice. Les avertissements et les anomalies sans localisation restent consultables, sans lien inventé. Les aperçus ne sont pas des captures de l'interface Windows et ne montrent pas automatiquement la zone exacte de l'anomalie.

Dépendance facultative : `pip install pymupdf`. Sans `--source-pdf`/`--target-pdf`, le rapport fonctionne sans aperçus.
