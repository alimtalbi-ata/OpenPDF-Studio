# OpenPDF Studio V41.4 — Défense contre les archives Office pathologiques
Auteur : Abdelhalim Talbi

## Protection du moteur de conversion
L'audit de sortie Office refuse désormais avant décompression :
- plus de 10 000 entrées ZIP ;
- plus de 512 Mio de taille totale décompressée annoncée ;
- une entrée de plus de 128 Mio.

Ces garde-fous limitent le risque de décompression disproportionnée de documents Office anormaux. Ils ne constituent pas une protection complète contre les archives malveillantes et doivent être complétés par des limites de temps et de mémoire.

## Qualification
Deux tests de régression ciblent les limites par entrée et par nombre d'entrées, avec fichiers PDF réels et métadonnées ZIP simulées. Aucun résultat de qualification n'est revendiqué avant la fin de la CI Windows.

## Roadmap
V41.5 : journal d'audit opt-in avec protection des données personnelles, rotation et export vérifiable.
