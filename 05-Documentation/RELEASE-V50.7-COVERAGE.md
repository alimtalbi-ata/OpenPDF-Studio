# OpenPDF Studio V50.7 — Vérification indépendante de la couverture RGB

Auteur : Abdelhalim Talbi. Cycle du 23 octobre 2026.

La compression automatique refuse une preuve RGB annonçant un nombre de pages, de pixels ou d'octets économisés différent du PDF. Une seconde lecture sans rendu supplémentaire vérifie la géométrie et la rotation de toutes les pages. L'échec est traité avant publication, sans écrasement. Le schéma JSON V50.6 est préservé pour compatibilité ; les champs coverage_verification et quality.coverage sont ajoutés.

Qualification : 12 nouveaux tests sur vrais PDF synthétiques à deux pages, rotation, reçus falsifiés ; régressions V50.6/V50.5/V50.4 Linux et Windows. Le workflow Windows natif doit être qualifié séparément. Les anciens exécutables ne sont pas des binaires V50.7.

Limites : contrôle de couverture et non deuxième mesure RGB ; aucune certification PDF/A, OCR, accessibilité, impression ou GUI. Aucun merge automatique.
