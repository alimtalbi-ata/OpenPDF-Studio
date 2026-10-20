# OpenPDF Studio V43.3 — Correctif de compatibilité Windows pour le découpage
Auteur : Abdelhalim Talbi

## Incident de qualification V43.2
GitHub Actions Windows run 39480904809 a échoué dans les tests de découpage transactionnel avec OSError [Errno 9] Bad file descriptor, sur os.fsync d'un fichier PDF ouvert en mode lecture seule.

## Correction
- Ouvrir les PDF de sortie en mode r+b lors du fsync, compatible avec le CRT Windows.
- Ne pas modifier les octets du PDF pendant cette synchronisation.
- Maintenir la vérification de source de V43.2.
- Ajouter un test de régression qui exécute le découpage et vérifie l'appel fsync.

## Qualification
La qualification V43.3 reste à confirmer. La réussite de CI n'équivaut pas à une validation GUI interactive.
