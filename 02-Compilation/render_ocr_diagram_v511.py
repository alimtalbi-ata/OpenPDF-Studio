"""Deterministic conceptual diagram, not a UI screenshot. Abdelhalim Talbi."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_diagram(path):
    path = Path(path)
    image = Image.new('RGB', (1600, 480), '#f7faff')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 23)
        title = ImageFont.truetype('DejaVuSans-Bold.ttf', 34)
    except OSError:
        font = ImageFont.load_default()
        title = font
    draw.text((55, 30), 'OpenPDF Studio V51.1 — OCR → Office éditable (circuit de contrôle)',
              font=title, fill='#183454')
    steps = [('1. PDF source', 'SHA-256 / scan'), ('2. OCR local', 'Tesseract / pages'),
             ('3. Qualité OCR', 'texte par page'), ('4. Conversion', 'DOCX/XLSX/PPTX'),
             ('5. Publication', 'audit / SHA-256')]
    for i, (heading, subtitle) in enumerate(steps):
        x, y = 55 + i * 312, 150
        draw.rounded_rectangle((x, y, x + 270, y + 170), radius=22,
                               fill='#e6f0fb', outline='#24629b', width=3)
        draw.text((x + 18, y + 42), heading, font=font, fill='#173d61')
        draw.text((x + 18, y + 92), subtitle, font=font, fill='#376183')
        if i < 4:
            draw.line((x + 270, y + 85, x + 307, y + 85), fill='#24629b', width=6)
            draw.polygon([(x + 307, y + 85), (x + 293, y + 77),
                          (x + 293, y + 93)], fill='#24629b')
    draw.text((55, 395), 'En cas d’échec : aucune sortie publiée. Schéma conceptuel, non capture UI ni preuve Windows.',
              font=font, fill='#a3343a')
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path
