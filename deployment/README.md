# Livraison Windows sans dépôt source

Cible : Windows 10/11 x64. Le poste destinataire reçoit uniquement les livrables compilés ; il ne doit pas avoir besoin de Python, pip, du SDK .NET, de Git, du dépôt ou d’un chemin du PC de compilation.

## Produire et distribuer

Compiler sur Windows : `02-Compilation\BUILD-WINDOWS-INSTALLER.cmd`.

Le fichier `OpenPDF-Studio-Portable-V40.2.exe`, ou l’installateur `OpenPDF-Studio-V40.2-Setup.exe`, dans `01-Application\binary`.

Python, PyMuPDF et Tk sont embarqués par PyInstaller ; Python ne doit pas être installé sur le poste destinataire.

Un EXE issu d’une compilation en dossier ne se distribue jamais seul : ses DLL et ressources doivent suivre. Une installation écrit les données utilisateur hors du dossier du programme. Les outils de compilation restent réservés au PC de développement.

## Tester sur un Windows propre

Le script voisin prépare une configuration Windows Sandbox avec réseau et presse-papiers désactivés. Il copie uniquement le dossier de distribution sélectionné, refuse les sources Python/C# et les liens, puis monte cette copie en lecture seule. Le dépôt n’est pas partagé avec la VM. Le dossier de rapports est le seul partage accessible en écriture. Windows Sandbox doit être activé sur un hôte compatible ; sinon utiliser une VM Windows neuve avec les mêmes fichiers.

Depuis la racine du dépôt, placer les seuls fichiers distribuables dans `C:\Livrables\Produit`, puis lancer :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deployment\Prepare-CleanWindowsTest.ps1 -Distribution C:\Livrables\Produit -Executable OpenPDF-Studio-Portable-V40.2.exe -OutputDirectory C:\Qualification\Essai-001
```

Ouvrir ensuite `C:\Qualification\Essai-001\Test-Clean-Windows.wsb`. Pour tester un installateur, préparer un dossier contenant uniquement le setup et passer son nom à `-Executable`, puis lancer l’application installée depuis la VM. Faire un essai portable et un essai installateur dans deux VM neuves. Ne pas utiliser le dépôt entier comme distribution.

Le script démarre le programme depuis un dossier différent contenant des espaces et supprime les variables de développement du processus. Il écrit les SHA-256 des fichiers testés et un rapport de démarrage. **Il n’attribue jamais PASS sur la seule création d’un processus** : le rapport reste `MANUAL_VALIDATION_REQUIRED` tant que les tests fonctionnels ne sont pas documentés.

Contrôles obligatoires : lancement sans outil de développement, interface utilisable, Créer deux petits PDF, les fusionner, ouvrir le résultat puis effectuer un découpage. Exécuter également `--self-test` et `--functional-self-test` sur le portable.

Tester aussi installation/désinstallation, conservation des données, lancement par un utilisateur standard, et absence de téléchargement requis pour les fonctions locales. Documenter séparément les fonctions qui requièrent un réseau ou un service distant. Noter dans `C:\DeliveryReports` la version Windows, les résultats, les prérequis absents et les captures utiles. Le contenu est conservé dans le dossier `reports` de l’hôte.

## État de validation

La préparation de ce protocole ne produit aucun EXE et ne prouve pas la compatibilité Windows. L’environnement cloud actuel est Linux : compilation native, exécution Windows et qualification sur machine propre restent à effectuer. Distribuer uniquement un artefact dont l’empreinte correspond aux rapports de qualification ; ne pas présenter un fichier de réservation comme un binaire.

L’autonomie d’exécution ne constitue pas une protection contre la rétro-ingénierie. Les bibliothèques et ressources nécessaires restent dans la distribution, même lorsque les fichiers du dépôt ne sont pas livrés.
