# OpenPDF Studio V50.6 — Compression mesurée et traçabilité des preuves

Auteur : Abdelhalim Talbi. 23 octobre 2026.

## Fonctionnalité livrée

V50.6 vérifie avant publication que l'audit RGB du moteur de compression
correspond exactement au PDF candidat (empreintes SHA-256 et tailles), à la
source, au profil et à la politique de qualité. Le rapport contient désormais
les pixels/pages comparés, la MAE maximale et la fraction de pixels modifiés.
Une preuve absente, incohérente ou non conforme entraîne le rejet du candidat.

## Qualification

- 11 tests V50.6 PASS ; 16 tests V50.5 PASS ; 11 tests benchmark V50.4 PASS.
- 12 tests de réconciliation PASS ; fermeture statique de 88 modules PASS.
- Résultats locaux Linux ; la CI Windows native et l'interface graphique
  sont des qualifications distinctes.

## Risques et limites

Le rendu RGB est mesuré à échelle bornée ; il ne certifie pas la fidélité
impression, OCR, PDF/A, signatures ou accessibilité. Les tests fonctionnels
utilisent des PDF synthétiques et non un corpus documentaire métier.

## Prochaine priorité

Qualification Windows réelle du portable et de l'installateur V50.6,
inspection de l'interface et corpus métier de compression multi-profils.
