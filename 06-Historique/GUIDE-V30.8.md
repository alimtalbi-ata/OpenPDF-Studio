# OpenPDF Studio V30.8 — Guide utilisateur
Auteur : Abdelhalim Talbi

Ouvrir OpenPDF Studio, utiliser F6 pour l’espace de travail ou Ctrl+K pour rechercher une action. Choisir un PDF source, puis une destination. Les conversions DOCX/XLSX/PPTX/TXT extraient principalement du texte éditable : la mise en page PDF et les tableaux ne sont pas garantis.

La conversion est écrite dans un fichier temporaire situé dans le dossier cible puis publiée atomiquement. Une annulation reçue avant publication empêche le remplacement du fichier de destination. L’annulation ne peut pas interrompre instantanément un convertisseur tiers déjà en cours d’exécution : elle est contrôlée avant et après celui-ci.

Sous Windows, lancer BUILD-WINDOWS-INSTALLER.cmd. Pour les EXE sans installateur, lancer BUILD-WINDOWS-EXE.cmd. Les scripts installent les dépendances de construction et requièrent winget si Python/Inno Setup manquent.
