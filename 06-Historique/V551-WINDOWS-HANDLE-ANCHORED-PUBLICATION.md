# Historique V551 — publication Windows native par handles

- **Auteur :** Abdelhalim Talbi.
- **Base :** V550 (\`feature/v51.4-handle-anchored-publication-v550-20261026\`, SHA initial \`aa014e0a6e511a01d1665ec0b40acd3f3f929dee\`).
- **Priorité :** remplacer le repli Windows basé sur chemins du primitive de publication atomique par une publication relative à des handles natifs.
- **Backend :** nouvelle source \`openpdf_windows_handle_publish_v551.py\`, appels \`NtCreateFile\` avec \`OBJ_DONT_REPARSE\`, ouverture du parent composant par composant, temporaire sans partage de suppression, publication exclusive par \`NtSetInformationFile(FileLinkInformation)\` et contrôle d'identité avant/après.
- **Intégration :** \`openpdf_atomic_output.publish_exclusive\` route les systèmes Windows vers le backend natif. Aucun fallback vers un lien par chemins n'est autorisé silencieusement.
- **Préconditions :** chemins locaux absolus à lettre de lecteur, répertoires ordinaires et système de fichiers acceptant les liens durs. Chemins UNC, lecteurs mappés, segments \`..\`, reparse points et configurations non prises en charge refusés.
- **Tests :** huit tests V551. Deux tests statiques/de refus exécutables sur Linux ; six tests natifs attendus sous Windows. La suite Windows doit s'exécuter sans skip avant toute qualification.
- **Preuve :** le reçu \`V551-CI-QUALIFICATION.json\` est produit uniquement à partir des logs Actions du SHA exact et du reçu parent V550 exact. Les fixtures des tests de parsing ne sont pas des preuves. Word/PDF sont régénérés depuis ce reçu.
- **Limite :** aucune revendication d'élimination complète de toutes les courses TOCTOU, de sécurité antivirus, de fidélité OCR/Office, de GUI humaine Windows ou de signature Authenticode.
- **Gouvernance :** PR brouillon empilée sur V550 ; \`main\` préservée, aucune fusion automatique.
