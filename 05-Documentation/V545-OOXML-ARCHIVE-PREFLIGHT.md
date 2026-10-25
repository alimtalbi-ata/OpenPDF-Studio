# OpenPDF Studio V545 — Intégrité OOXML et chemins ambigus

**Auteur : Abdelhalim Talbi**  
**Base :** V544.1 / PR #51. La version applicative demeure 51.4. Cette évolution porte sur les contrôles du qualificateur Office utilisé par la chaîne PDF → DOCX/XLSX/PPTX ; elle ne prétend pas améliorer à elle seule la fidélité visuelle d'une conversion.

## Risque traité

Avant V545, la prévalidation inspectait la table centrale ZIP et les relations pertinentes, mais ne vérifiait pas systématiquement le CRC de chaque contenu. Un composant personnalisé inutilisé et corrompu pouvait donc rester non lu par l'analyseur OOXML de plus haut niveau. Les noms étaient également comparés au sens exact ; des noms qui ne diffèrent que par la casse ou par des normalisations de nom de fichier Windows pouvaient rendre un paquet ambigu entre outils et plateformes.

## Modification

- Après les contrôles de taille, de ratio, de liens, de contenu actif et de relations externes, tous les membres sont lus par `ZipFile.testzip()`. Toute erreur de décompression ou de CRC devient un refus explicite, sans exposer le nom du membre fautif dans les diagnostics.
- Les noms sont vérifiés après normalisation Unicode NFKC et comparaison insensible à la casse. Les collisions normalisées sont refusées.
- Les chemins qui changeraient de structure à la normalisation, les composants `.`/`..`, les séparateurs ambigus, les noms terminés par un point ou une espace et les noms de périphériques Windows réservés (`CON`, `PRN`, `AUX`, `NUL`, `COM1…COM9`, `LPT1…LPT9`) sont refusés.
- Les limites préexistantes restent en place : archive ≤ 32 Mio, ≤ 2 048 membres, membre ≤ 8 Mio, total décompressé ≤ 64 Mio, ratio maximal 500:1, ainsi que les contrôles de contenu actif, de symlink, de chiffrement et de relation externe.
- Le manifeste SHA-256 de sources est actualisé pour le module touché. Aucun nouveau module d'exécution n'est ajouté.

## Tests de non-régression

Le nouveau jeu V545 utilise des DOCX/XLSX générés par les tests, pas de données utilisateur. Il vérifie un paquet valide, une collision `WORD/DOCUMENT.XML`, un nom terminé par un point, un nom de périphérique réservé et la corruption CRC d'un membre personnalisé non référencé. La CI ciblée exécute ces tests et la suite V542 sous Ubuntu 24.04 et Windows Server 2022.

## Portée et limites

La vérification CRC confirme la cohérence interne ZIP ; elle ne prouve pas l'authenticité de l'auteur ni l'absence de malware. Les plafonds de ressources limitent le travail de décompression, mais ces contrôles ne remplacent pas une analyse antivirus ou une revue spécialisée de sécurité. Cette évolution ne mesure ni précision OCR, ni fidélité métier, géométrique, typographique ou visuelle des documents convertis.

**Qualification Windows réelle :** elle ne sera considérée comme réussie qu'après les jobs Windows natifs de la CI. Aucun résultat graphique humain Windows ni aucun nouveau binaire n'est présumé par cette note.
