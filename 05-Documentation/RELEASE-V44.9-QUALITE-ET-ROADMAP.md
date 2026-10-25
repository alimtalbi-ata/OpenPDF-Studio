# OpenPDF Studio V44.9 — Images PDF vers Word
Auteur : Abdelhalim Talbi

Le convertisseur PDF vers DOCX conserve désormais les images intégrées accessibles via PyMuPDF, en les insérant comme images Word, en plus du texte éditable. Un test de bout en bout génère un PDF contenant texte et image PNG, exécute le dispatcher public, puis vérifie que le DOCX comporte le texte et une image embarquée.

Limites : positions et dimensions approximatives, tableaux complexes non reconstruits, polices non garanties, formats d'images PDF non supportés indiqués par un marqueur. La qualité doit être validée avec des documents utilisateurs. OCR autonome Windows encore non qualifié.
