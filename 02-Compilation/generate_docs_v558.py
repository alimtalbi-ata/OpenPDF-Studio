"""Generate V558 Word/PDF release notes and honest architecture diagrams.
The diagram is generated artwork, not an application screenshot.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = "Abdelhalim Talbi"
TITLE = "OpenPDF Studio V51.4 / V558 - PDF and Office visual fidelity"
DOCX_NAME = "OpenPDF-Studio-V51.4-V558-Visual-Fidelity-Guide.docx"
PDF_NAME = "OpenPDF-Studio-V51.4-V558-Visual-Fidelity-Guide.pdf"
PNG_NAME = "Architecture-V558-Visual-Fidelity.png"
SVG_NAME = "Architecture-V558-Visual-Fidelity.svg"


def build_context(*, commit_sha=None, pr_number=None, workflow_run_id=None):
    sha = commit_sha
    if sha is None:
        sha = os.environ.get("OPENPDF_HEAD_SHA") or os.environ.get("GITHUB_SHA", "")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        sha = "NOT-VERIFIED"
    pr = str(pr_number if pr_number is not None else os.environ.get("OPENPDF_PULL_REQUEST_NUMBER", "")).strip()
    run_id = str(workflow_run_id if workflow_run_id is not None else os.environ.get("OPENPDF_RUN_ID", "")).strip()
    return {
        "commit_sha": sha,
        "pr_number": pr if pr.isdigit() else "not supplied",
        "workflow_run_id": run_id if run_id.isdigit() else "not supplied",
    }


def build_sections(context):
    sha_verified = context["commit_sha"] != "NOT-VERIFIED"
    pr_url = ("https://github.com/alimtalbi-ata/OpenPDF-Studio/pull/" + context["pr_number"]
              if context["pr_number"].isdigit() else "not available")
    run_url = ("https://github.com/alimtalbi-ata/OpenPDF-Studio/actions/runs/" + context["workflow_run_id"]
               if context["workflow_run_id"].isdigit() else "not available")
    return [
        ("1. Objectif produit",
         "La qualite d'une conversion PDF vers Word, Excel ou PowerPoint ne se resume pas au nombre de mots "
         "retrouves. V558 compare un PDF source avec un PDF de rendu fourni pour le fichier Office candidat, "
         "et mesure la rasterisation en niveaux de gris, les dimensions des pages, la position des boites de "
         "mots, la precision/rappel des tokens et leur ordre d'extraction."),
        ("2. Utilisation",
         "Creer un manifeste JSON contenant 2 a 32 cas. Chaque cas lie par SHA-256 le PDF source, le document "
         "DOCX/XLSX/PPTX, le PDF de rendu et une annotation. Le PDF de rendu doit etre exporte avec un moteur "
         "Office declare. Le CLI refuse les chemins absolus, les liens symboliques, les preuves changees, les "
         "documents OOXML actifs/non conformes, les PDF chiffres et les depassements de budgets."),
        ("3. Mesures",
         "Le raster est compare a 96 dpi en niveaux de gris. Le rapport calcule l'erreur absolue moyenne sur "
         "255, la fraction de pixels modifies, les ecarts de dimensions, le precision/rappel du texte, le rappel "
         "d'ordre par LCS exacte et l'IoU/le decalage moyen des boites de mots appariees. Les seuils sont "
         "explicites dans le manifeste et la decision utilise les valeurs non arrondies."),
        ("4. Confidentialite et integrity",
         "Le recu est agrege : aucun texte PDF, nom de fichier ni chemin n'est exporte. Les entrees sont bornees "
         "en taille, pages, pixels et tokens. Les SHA-256 relient le manifeste et les preuves aux octets testes; "
         "ils ne signent pas l'editeur et ne prouvent pas qu'un moteur a reellement produit le PDF fourni."),
        ("5. Provenance et limites",
         "Le nom et la version du moteur sont declares dans l'annotation, non attestes. Les boites de mots "
         "utilisent l'appariement de sequence pour mesurer une derive moyenne; elles ne constituent pas une "
         "validation de mise en page par un humain. La comparaison raster depend du rendu PDF et de la resolution. "
         "Les tests automatiques V558 utilisent des documents synthetiques, pas un corpus metier humainement annote. "
         "Aucune capture d'ecran de l'application n'est incluse."),
        ("6. Qualification",
         "Les tests unitaires et fonctionnels de la suite V558 doivent passer sur Ubuntu et Windows dans la CI. "
         "La fermeture des sources et les checksums du manifeste sont des controles statiques. La construction "
         "native Windows, le smoke test, l'installation/desinstallation et le ZIP cumulatif sont des etapes "
         "distinctes; cette documentation ne les considere pas PASS par anticipation."),
        ("7. Structure des donnees",
         "Le manifeste contient schema, cases et thresholds. Les cas referencent source_pdf, office_file, "
         "rendered_pdf et annotations. L'annotation lie les trois SHA-256 et contient origin, renderer et "
         "renderer_version. Seule une origine human_reviewed compte pour le seuil humain, et cette mention "
         "reste une declaration, pas une attestation cryptographique."),
        ("Traceabilite",
         "Commit: " + context["commit_sha"] + "\nPR: " + pr_url + "\nWorkflow: " + run_url + "\n" +
         ("Le SHA a le format attendu; les recus doivent confirmer la qualification exacte de ce commit."
          if sha_verified else
          "Le SHA source est absent ou invalide; ce document est explicitement non qualifie.")),
    ]


def svg_diagram():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420" role="img" aria-labelledby="title desc">
<title id="title">OpenPDF Studio V558 PDF and Office visual fidelity</title>
<desc id="desc">Generated architecture diagram, not an application screenshot. Declared renderer provenance is not independently attested.</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#24566b"/></marker></defs>
<rect x="28" y="76" width="250" height="160" rx="12" fill="#e8f3f5" stroke="#24566b" stroke-width="2"/>
<text x="153" y="110" text-anchor="middle" font-family="Arial" font-size="17" fill="#153747">PDF source</text>
<text x="153" y="141" text-anchor="middle" font-family="Arial" font-size="13" fill="#153747">SHA-256 + text layer</text>
<text x="153" y="166" text-anchor="middle" font-family="Arial" font-size="13" fill="#153747">page geometry / raster</text>
<text x="153" y="191" text-anchor="middle" font-family="Arial" font-size="13" fill="#153747">bounded pixel budget</text>
<rect x="28" y="266" width="250" height="110" rx="12" fill="#f2eafe" stroke="#6750a4" stroke-width="2"/>
<text x="153" y="299" text-anchor="middle" font-family="Arial" font-size="16" fill="#3e2d73">DOCX / XLSX / PPTX</text>
<text x="153" y="324" text-anchor="middle" font-family="Arial" font-size="12" fill="#3e2d73">OOXML CRC + active-content</text>
<text x="153" y="346" text-anchor="middle" font-family="Arial" font-size="12" fill="#3e2d73">and path preflight</text>
<path d="M278 320 L350 320 L350 210 L408 210" stroke="#24566b" stroke-width="3" fill="none" marker-end="url(#arrow)"/>
<path d="M278 156 L408 156" stroke="#24566b" stroke-width="3" fill="none" marker-end="url(#arrow)"/>
<rect x="416" y="90" width="340" height="192" rx="12" fill="#fff3df" stroke="#a75c19" stroke-width="2"/>
<text x="586" y="124" text-anchor="middle" font-family="Arial" font-size="17" fill="#75410d">V558 comparator</text>
<text x="586" y="156" text-anchor="middle" font-family="Arial" font-size="13" fill="#75410d">grayscale MAE / changed pixels</text>
<text x="586" y="182" text-anchor="middle" font-family="Arial" font-size="13" fill="#75410d">page dimensions + word-box IoU</text>
<text x="586" y="208" text-anchor="middle" font-family="Arial" font-size="13" fill="#75410d">token precision / recall / LCS</text>
<text x="586" y="234" text-anchor="middle" font-family="Arial" font-size="13" fill="#75410d">SHA-bound input rechecks</text>
<path d="M756 186 L832 186" stroke="#24566b" stroke-width="3" fill="none" marker-end="url(#arrow)"/>
<rect x="840" y="90" width="330" height="192" rx="12" fill="#e7f5e9" stroke="#2b7545" stroke-width="2"/>
<text x="1005" y="124" text-anchor="middle" font-family="Arial" font-size="17" fill="#1d5833">Privacy-safe report</text>
<text x="1005" y="156" text-anchor="middle" font-family="Arial" font-size="13" fill="#1d5833">explicit thresholds / PASS-FAIL</text>
<text x="1005" y="182" text-anchor="middle" font-family="Arial" font-size="13" fill="#1d5833">no paths or document text</text>
<text x="1005" y="208" text-anchor="middle" font-family="Arial" font-size="13" fill="#1d5833">renderer declared, not attested</text>
<text x="1005" y="234" text-anchor="middle" font-family="Arial" font-size="13" fill="#1d5833">no fabricated UI screenshots</text>
<rect x="416" y="318" width="754" height="58" rx="8" fill="#f6f6f6" stroke="#666" stroke-width="1.5"/>
<text x="793" y="341" text-anchor="middle" font-family="Arial" font-size="13" fill="#333">Fail closed: hash mismatch, unsafe OOXML, missing text, resource budget or threshold failure</text>
<text x="793" y="361" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">Architecture diagram only - not a screenshot or renderer attestation.</text>
</svg>"""


def draw_diagram_png(path):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1200, 420), "white")
    draw = ImageDraw.Draw(image)
    font_path = next((str(candidate) for candidate in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ) if candidate.is_file()), None)
    title_font = ImageFont.truetype(font_path, 17) if font_path else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 13) if font_path else ImageFont.load_default()

    boxes = [
        (28, 76, 278, 236, "#e8f3f5", "#24566b", "PDF source",
         ["SHA-256 + text layer", "page geometry / raster", "bounded pixel budget"]),
        (28, 266, 278, 376, "#f2eafe", "#6750a4", "DOCX / XLSX / PPTX",
         ["OOXML CRC + active-content", "and path preflight"]),
        (416, 90, 756, 282, "#fff3df", "#a75c19", "V558 comparator",
         ["grayscale MAE / changed pixels", "page dimensions + word-box IoU",
          "token precision / recall / LCS", "SHA-bound input rechecks"]),
        (840, 90, 1170, 282, "#e7f5e9", "#2b7545", "Privacy-safe report",
         ["explicit thresholds / PASS-FAIL", "no paths or document text",
          "renderer declared, not attested", "no fabricated UI screenshots"]),
    ]
    for x0, y0, x1, y1, fill, outline, title, rows in boxes:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=fill, outline=outline, width=2)
        tw = draw.textbbox((0, 0), title, font=title_font)
        draw.text(((x0 + x1 - (tw[2] - tw[0])) / 2, y0 + 18), title, fill=outline, font=title_font)
        for n, row in enumerate(rows):
            draw.text((x0 + 12, y0 + 58 + n * 24), row, fill="#222222", font=body_font)

    def arrow(points):
        draw.line(points, fill="#24566b", width=3, joint="curve")
        x0, y0 = points[-2]
        x1, y1 = points[-1]
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) >= abs(dy):
            sign = 1 if dx >= 0 else -1
            head = [(x1, y1), (x1 - sign * 11, y1 - 6), (x1 - sign * 11, y1 + 6)]
        else:
            sign = 1 if dy >= 0 else -1
            head = [(x1, y1), (x1 - 6, y1 - sign * 11), (x1 + 6, y1 - sign * 11)]
        draw.polygon(head, fill="#24566b")

    arrow([(278, 156), (360, 156), (360, 170), (416, 170)])
    arrow([(278, 320), (350, 320), (350, 220), (416, 220)])
    arrow([(756, 186), (840, 186)])
    draw.rounded_rectangle((416, 318, 1170, 376), radius=8, fill="#f6f6f6", outline="#666666", width=1)
    draw.text((435, 331), "Fail closed: hash mismatch, unsafe OOXML, missing text, budget or threshold failure",
              fill="#333333", font=body_font)
    draw.text((435, 354), "Architecture diagram only - not a screenshot or renderer attestation.",
              fill="#333333", font=body_font)
    image.save(path, format="PNG", optimize=True)


def generate(output_dir=None, *, commit_sha=None, pr_number=None, workflow_run_id=None):
    from docx import Document
    from docx.shared import Inches, Pt
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image as ReportImage, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    )

    context = build_context(commit_sha=commit_sha, pr_number=pr_number, workflow_run_id=workflow_run_id)
    output = Path(output_dir) if output_dir else ROOT / "05-Documentation"
    output.mkdir(parents=True, exist_ok=True)
    docx_path, pdf_path = output / DOCX_NAME, output / PDF_NAME
    png_path, svg_path = output / PNG_NAME, output / SVG_NAME
    svg_path.write_text(svg_diagram(), encoding="utf-8")
    draw_diagram_png(png_path)
    sections = build_sections(context)

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)
    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9)
    doc.add_heading(TITLE, 0)
    doc.add_paragraph("Auteur : " + AUTHOR)
    doc.add_paragraph("Version applicative 51.4 ; V558 est un jalon de developpement.")
    doc.add_heading("Vue d'architecture", level=1)
    doc.add_picture(str(png_path), width=Inches(6.35))
    doc.add_paragraph("Schema d'architecture genere automatiquement ; ce n'est pas une capture d'ecran.")
    for heading, body in sections:
        doc.add_heading(heading, level=1)
        for paragraph in body.split("\n"):
            if paragraph:
                doc.add_paragraph(paragraph)
    doc.add_heading("Metriques du rapport", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Shading Accent 1"
    table.rows[0].cells[0].text = "Mesure"
    table.rows[0].cells[1].text = "Interpretation"
    for metric, definition in (
        ("Erreur raster moyenne", "MAE en niveaux de gris, 0 a 255, sur les pages communes."),
        ("Pixels modifies", "Fraction de pixels dont la difference depasse le seuil fixe 16/255."),
        ("Precision / rappel texte", "Tokens d'extraction apparies, comparant le PDF source au PDF rendu."),
        ("Rappel d'ordre", "LCS exacte des tokens extraits ; pas un ordre de lecture visuel humain."),
        ("IoU et derive des mots", "Boites normalisees des mots apparies par sequence."),
        ("Dimensions et pages", "Maximum d'ecart de page, signale separement du score raster."),
    ):
        row = table.add_row().cells
        row[0].text, row[1].text = metric, definition
    doc.save(docx_path)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="V558Title", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=19, leading=24, alignment=TA_LEFT, spaceAfter=5 * mm))
    styles.add(ParagraphStyle(name="V558Section", parent=styles["Heading2"], fontSize=12,
                              leading=15, textColor=colors.HexColor("#24566b"), spaceBefore=4 * mm))
    styles.add(ParagraphStyle(name="V558Body", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=2 * mm))
    story = [
        Paragraph(escape(TITLE), styles["V558Title"]),
        Paragraph("Auteur : " + escape(AUTHOR), styles["V558Body"]),
        Paragraph("Version applicative 51.4 ; V558 est un jalon de developpement.", styles["V558Body"]),
        Spacer(1, 3 * mm),
        ReportImage(str(png_path), width=175 * mm, height=61.25 * mm),
        Paragraph("Schema d'architecture genere automatiquement ; ce n'est pas une capture d'ecran.",
                  styles["V558Body"]),
    ]
    for heading, body in sections:
        story.append(Paragraph(escape(heading), styles["V558Section"]))
        for paragraph in body.split("\n"):
            if paragraph:
                story.append(Paragraph(escape(paragraph), styles["V558Body"]))
    rows = [[Paragraph("<b>Mesure</b>", styles["V558Body"]),
             Paragraph("<b>Interpretation</b>", styles["V558Body"])]]
    for metric, definition in (
        ("Erreur raster moyenne", "MAE en niveaux de gris, 0 a 255, sur les pages communes."),
        ("Pixels modifies", "Fraction des pixels avec difference superieure a 16/255."),
        ("Precision / rappel texte", "Couverture multiensemble des tokens extraits."),
        ("Rappel d'ordre", "LCS exacte du texte extrait, pas l'ordre visuel humain."),
        ("IoU / derive", "Comparaison des boites de mots en coordonnees normalisees."),
        ("Pages / dimensions", "Controle separe du nombre et de la taille des pages."),
    ):
        rows.append([Paragraph(escape(metric), styles["V558Body"]),
                     Paragraph(escape(definition), styles["V558Body"])])
    table = Table(rows, colWidths=[43 * mm, 132 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f3f5")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9bb3bb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([Spacer(1, 3 * mm), table])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(16 * mm, 10 * mm, "OpenPDF Studio V558 - " + AUTHOR)
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=16 * mm,
                      leftMargin=16 * mm, topMargin=14 * mm, bottomMargin=17 * mm,
                      title=TITLE, author=AUTHOR).build(story, onFirstPage=footer, onLaterPages=footer)
    return {"docx": str(docx_path), "pdf": str(pdf_path), "png": str(png_path), "svg": str(svg_path)}


if __name__ == "__main__":
    paths = generate()
    for key, value in paths.items():
        print(f"{key}: {value}")
