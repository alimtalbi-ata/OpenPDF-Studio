# OpenPDF Studio V50.0 - Extraction non contigue

Auteur : **Abdelhalim Talbi**. Date : 23 octobre 2026.

## Fonctionnalite

L'operation Extraction accepte une selection facultative de pages : `!paires`, `1,4,6`, `5-3`, `toutes,!paires,6`. Le controleur reutilise le parseur borne de reorganisation et le service PDF existant ; la selection prime sur Debut/Fin lorsqu'elle est renseignee. Une selection vide conserve le comportement historique.

## Qualification verifiee

- Linux local, sources cumulatives V50.0 : **978 tests reussis, 0 echec, 0 erreur** dans la suite `04-Tests-et-Qualification`.
- Nouveaux tests fonctionnels V50.0 : **12/12 PASS** sur de vrais PDF PyMuPDF.
- GitHub Actions `39947744317` : **12 tests PASS sur Ubuntu et 12 sur Windows**, journaux controles.
- CI existante de reorganisation `39947743915` : Ubuntu et Windows **SUCCESS**.
- ZIP source cumulatif avec manifestes SHA-256 : genere localement, sans executable Windows V50.0 qualifie.

## Limites

Les modules du depot GitHub restent partiellement plus anciens que le ZIP cumulatif local ; cette PR est empilee sur #4, pas fusionnee. La CI Windows teste des modules Python et **ne qualifie pas** le binaire PyInstaller, l'installation Inno Setup ni les parcours GUI. Les captures UI Windows reelles ne sont pas disponibles. Les tests historiques du dossier `03-Sources` ne sont pas declares conformes.

## Priorite suivante

Reconcilier les sources cumulatives, lancer le build Windows autonome via `BUILD-OPENPDF-WINDOWS.cmd`, verifier installation/lancement/desinstallation et qualifier les conversions Office sur corpus representatif. Ne pas fusionner automatiquement dans `main`.
