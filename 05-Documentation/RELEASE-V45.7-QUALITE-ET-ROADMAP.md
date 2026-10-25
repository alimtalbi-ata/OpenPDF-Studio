# OpenPDF Studio V45.7 — correction de la porte de publication
Auteur : Abdelhalim Talbi

Le test OCR exécuté dans les deux binaires V45.6 a réussi. L'échec de publication était dû à deux contrôles historiques `openpdf_bind_smoke.py` et `openpdf_release_gate.py` qui exigeaient exactement deux tests de démarrage alors que V45.6 en exécute désormais trois. Les deux contrôles exigent maintenant trois tests réussis, y compris le test OCR embarqué. Aucune porte de sécurité n'a été désactivée.

La qualification Windows V45.7 reste à confirmer. Les tests sur un Windows sans Tesseract installé et les essais manuels d'interface restent distincts.
