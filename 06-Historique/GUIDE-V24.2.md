# OpenPDF Studio V24.2 — Guide de synchronisation contrôlée

Auteur : Abdelhalim Talbi

1. Ouvrir le diagnostic HTML produit par `diagnostic_dashboard.build_dashboard`.
2. Naviguer entre les paires avec **Page précédente / Page suivante**.
3. Consulter **Correspondance** : seuls les appariements `exact-text` explicites autorisent le défilement synchronisé.
4. Décochez **Défilement synchronisé** pour comparer librement. Ce choix est conservé lors de la navigation.
5. Les pages candidates ou sans paire désactivent et décochent le contrôle. Le choix utilisateur est restauré seulement si une paire `exact-text` est retrouvée.

Les preuves d'appariement sont déclarées dans le rapport. Elles ne garantissent pas la fidélité visuelle ou l'identité des régions. Captures Chromium Linux réelles, aucune recette native Windows.
