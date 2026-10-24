"""V51.4-specific Word/PDF documentation and architecture. Author: Abdelhalim Talbi.
Only real Linux Xvfb screenshots are embedded when present; never synthesize Windows evidence.
"""
from pathlib import Path
from docx import Document
from docx.shared import Inches
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / '05-Documentation'
TITLE = 'OpenPDF Studio V51.4 — Tableaux Excel éditables et livraison Windows'
SECTIONS = [
 ('Fonctionnalité', 'Le mode Excel enrichi est désactivé par défaut. La feuille historique Texte PDF est conservée. Chaque tableau géométrique reconnu reçoit une feuille éditable avec provenance et contrôle cellule par cellule. Les formules issues du PDF restent du texte.'),
 ('Parcours utilisateur', 'Ajouter un PDF, sélectionner Vers Excel, activer Tableaux en feuilles Excel éditables, choisir une nouvelle destination XLSX et exécuter. Pour un PDF numérisé, effectuer auparavant un OCR PDF séparé. La combinaison OCR Office et tableaux est refusée.'),
 ('Sécurité', 'Réservation de destination, refus des sorties existantes et symboliques, contrôle SHA-256 source, audit OOXML et comparaison des cellules avant publication. Nettoyage des fichiers temporaires en cas d’échec.'),
 ('Fidélité et limites', 'La détection PyMuPDF est heuristique. Les cellules fusionnées, tableaux sans bordures et mises en page complexes peuvent être mal détectés. Les valeurs doivent être contrôlées sur le document métier.'),
 ('Windows autonome', 'Lancer BUILD-OPENPDF-WINDOWS.cmd à la racine. Python 3.12, modèles OCR eng/fra, PyInstaller et Inno Setup sont préparés pendant le build. VERSION.txt vaut 51.4 et le manifeste impose 94 modules.'),
 ('Qualification', 'Suite locale Linux : 1 176 tests réussis. Douze nouveaux tests GUI/dispatcher réussis. Fermeture statique : 94 modules requis. CI native Windows #40051065571 : portable, installateur, OCR réel, installation et désinstallation silencieuses réussis. Aucun test GUI Windows humain.'),
 ('Preuves et risques', 'Une capture V51.4-GUI-Linux-Xvfb-REAL.png est une capture Linux Xvfb réelle, jamais une preuve Windows. Les binaires ne sont pas signés Authenticode. Prochaine priorité : corpus de tableaux métier complexes et validation GUI Windows humaine.')
]

def build():
    DOCS.mkdir(exist_ok=True)
    diagram = DOCS / 'Architecture-V51.4-Pipeline.png'
    im = PILImage.new('RGB', (1400, 260), 'white')
    draw = ImageDraw.Draw(im)
    for label, x in [('PDF source',30), ('Prévalidation',280), ('XLSX + tableaux',530), ('Audit cellules',780), ('Publication',1030)]:
        draw.rounded_rectangle((x,70,x+215,185),radius=18,outline='#176a7b',fill='#e6f3f5',width=4)
        draw.text((x+18,116),label,fill='#153a4b')
        if x < 1000:
            draw.line((x+215,125,x+245,125),fill='#22627a',width=5)
            draw.polygon([(x+245,125),(x+230,117),(x+230,133)],fill='#22627a')
    draw.text((30,220),'Rejet sans écrasement si validation ou fidélité échoue',fill='#a33333')
    im.save(diagram)
    doc = Document()
    doc.add_heading(TITLE, 0)
    doc.add_paragraph('Auteur : Abdelhalim Talbi | 24 octobre 2026')
    doc.add_paragraph('Qualification Linux, CI Windows automatisée ; validation GUI Windows humaine non réalisée.')
    doc.add_picture(str(diagram), width=Inches(6))
    for i, (heading, body) in enumerate(SECTIONS):
        if i in (3, 5): doc.add_page_break()
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
    capture = DOCS / 'V51.4-GUI-Linux-Xvfb-REAL.png'
    if capture.is_file():
        doc.add_heading('Capture réelle — Linux Xvfb, pas Windows', level=1)
        doc.add_picture(str(capture), width=Inches(5.9))
    doc.save(DOCS / 'OpenPDF-Studio-V51.4-Guide.docx')
    styles = getSampleStyleSheet()
    story = [Paragraph(TITLE, styles['Title']), Spacer(1, 12), Paragraph('Auteur : Abdelhalim Talbi', styles['Normal']), Spacer(1, 12), Image(str(diagram), width=470, height=87)]
    for i, (heading, body) in enumerate(SECTIONS):
        if i in (3, 5): story.append(PageBreak())
        story += [Spacer(1, 14), Paragraph(heading, styles['Heading2']), Paragraph(body, styles['BodyText'])]
    if capture.is_file():
        story += [PageBreak(), Paragraph('Capture réelle — Linux Xvfb, pas Windows', styles['Heading2']), Image(str(capture), width=480, height=333)]
    SimpleDocTemplate(str(DOCS / 'OpenPDF-Studio-V51.4-Guide.pdf'), pagesize=A4).build(story)

if __name__ == '__main__':
    build()
