"""Generate a current V51.4 Word/PDF guide tied to V548 CI receipts.

When no matching CI receipt exists (offline local build), explicitly report
that qualification is unverified. Never carry forward stale test counts.
Author: Abdelhalim Talbi.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

from PIL import Image as PILImage, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "05-Documentation"
TITLE = "OpenPDF Studio V51.4 — Opérations PDF, conversions Office et sécurité des sources"
CI_SCHEMA = "openpdf.v548.ci-qualification.v1"
MODULE_MANIFEST = "07-Manifestes/V51.4-REQUIRED-RUNTIME-MODULES.json"
CI_REPORT = "04-Tests-et-Qualification/V548-CI-QUALIFICATION.json"


def required_module_count(root=ROOT):
    """Read the current runtime closure rather than embedding a historical count."""
    data = json.loads((Path(root) / MODULE_MANIFEST).read_text(encoding="utf-8-sig"))
    modules = data.get("modules")
    if (not isinstance(modules, list) or not modules or
            any(not isinstance(item, str) for item in modules) or
            len(modules) != len(set(modules))):
        raise ValueError("Manifeste des modules runtime invalide")
    if "openpdf_source_path_guard_v548" not in modules:
        raise ValueError("Le manifeste runtime n'inclut pas le garde V548")
    return len(modules)


def current_head_sha(root=ROOT):
    for key in ("OPENPDF_HEAD_SHA", "GITHUB_SHA"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root), check=True, capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def load_current_ci_report(root=ROOT, expected_head_sha=None):
    """Return only a qualified receipt for this exact source revision."""
    path = Path(root) / CI_REPORT
    if not path.is_file() or path.is_symlink():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return None
        if data.get("schema") != CI_SCHEMA or data.get("version") != "51.4":
            return None
        if data.get("qualified") is not True or not data.get("commit_sha"):
            return None
        head = expected_head_sha or current_head_sha(root)
        if head and data.get("commit_sha") != head:
            return None
        if data.get("module_count") != required_module_count(root):
            return None

        page = data.get("page_order")
        if not isinstance(page, dict):
            return None
        if (page.get("head_sha") != data.get("commit_sha") or
                page.get("status") != "completed" or
                page.get("conclusion") != "success"):
            return None
        jobs = page.get("jobs")
        tests = page.get("tests")
        if not isinstance(jobs, dict) or not isinstance(tests, dict):
            return None
        for platform in ("ubuntu", "windows"):
            job = jobs.get(platform)
            item = tests.get(platform)
            if not isinstance(job, dict) or not isinstance(item, dict):
                return None
            if job.get("status") != "completed" or job.get("conclusion") != "success":
                return None
            expected = item.get("expected")
            passed = item.get("passed")
            skipped = item.get("skipped")
            failed = item.get("failed")
            numbers = (expected, passed, skipped, failed)
            if any(type(value) is not int or value < 0 for value in numbers):
                return None
            if (expected <= 0 or failed != 0 or skipped != 0 or passed != expected or
                    item.get("conclusion") != "success"):
                return None

        source = data.get("source_closure")
        if not isinstance(source, dict):
            return None
        prerequisites = source.get("prerequisite_jobs")
        native = source.get("native_windows")
        if not isinstance(prerequisites, dict) or not prerequisites:
            return None
        if not isinstance(native, dict):
            return None
        for key in ("portable", "installer", "installation"):
            if not isinstance(native.get(key), dict):
                return None
        if (native["portable"].get("smoke_passed") is not True or
                native["installer"].get("smoke_passed") is not True or
                native["installation"].get("passed") is not True):
            return None
        for job in prerequisites.values():
            if not isinstance(job, dict) or job.get("status") != "completed" or job.get("conclusion") != "success":
                return None
        return data
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        return None

def _ci_summary(report):
    if report is None:
        return (
            "Qualification V548 de cette révision : NON VÉRIFIÉE. Aucun reçu CI correspondant "
            "à ce commit n'est disponible dans cet environnement ; aucun résultat de test ou "
            "de build Windows n'est revendiqué. Une compilation locale hors CI ne remplace pas "
            "les tests Ubuntu/Windows ni la qualification native."
        )
    ubuntu = report["page_order"]["tests"]["ubuntu"]
    windows = report["page_order"]["tests"]["windows"]
    native = report["source_closure"]["native_windows"]
    page = report["page_order"]
    source = report["source_closure"]
    lines = [
        (
            "Tests fonctionnels V548 sur les composants PDF : Ubuntu "
            f"{ubuntu['passed']}/{ubuntu['expected']} réussis, {ubuntu['skipped']} ignorés, "
            f"{ubuntu['failed']} échoué(s) ; Windows "
            f"{windows['passed']}/{windows['expected']} réussis, {windows['skipped']} ignorés, "
            f"{windows['failed']} échoué(s). Les jobs de réorganisation de pages ont terminé "
            "avec succès sur les deux systèmes."
        ),
        (
            "Fermeture des sources et régressions : PASS sur Ubuntu et Windows. "
            "Le manifeste runtime courant contient "
            f"{report['module_count']} modules distincts, dont le garde V548."
        ),
        (
            f"Portable Windows : PASS ({native['portable']['bytes']:,} octets, "
            f"SHA-256 {native['portable']['sha256']}); smoke "
            f"{native['portable']['checks_passed']}/{native['portable']['checks_passed']} "
            "contrôles réussis."
        ),
        (
            f"Installateur Windows : PASS ({native['installer']['bytes']:,} octets, "
            f"SHA-256 {native['installer']['sha256']}); installation, lancement, OCR et "
            "désinstallation silencieuse réussis."
        ),
        (
            f"CI page-order : run #{page['run_id']} — {page['url']}. "
            f"Fermeture et qualification native Windows : run #{source['run_id']} — {source['url']}."
        ),
        (
            "Le reçu final de taille, inventaire, CRC et SHA-256 du ZIP cumulatif est produit "
            "par l'étape de packaging après la génération du présent guide ; il reste une preuve séparée."
        ),
    ]
    return "\n".join(lines)


def build_sections(root=ROOT, report=None):
    modules = required_module_count(root)
    return [
        (
            "Fonctionnalités",
            "Les opérations PDF comprennent la fusion, le découpage, l'extraction et la réorganisation, "
            "ainsi que la compression contrôlée. OCR et conversions vers DOCX, XLSX et PPTX sont disponibles "
            "selon le type d'entrée et les contrôles de publication. La fidélité visuelle des conversions "
            "éditables n'est pas garantie par défaut."
        ),
        (
            "Parcours utilisateur",
            "Sélectionner le PDF source, choisir une opération et une nouvelle destination, régler les "
            "paramètres disponibles puis exécuter. Les PDF numérisés peuvent nécessiter un OCR préalable. "
            "Les opérations refusées ne doivent jamais publier une sortie partielle."
        ),
        (
            "Sécurité — garde V548 du chemin source",
            "Le garde parcourt le chemin lexical absolu composant par composant avant toute canonicalisation. "
            "Les liens symboliques et jonctions Windows dans les répertoires parents comme dans le fichier "
            "final sont refusés ; un segment '..' ne peut pas masquer un lien rencontré plus tôt. "
            "La garde est intégrée au dispatcher des opérations PDF et conversions Office, ainsi qu'au service "
            "de pages atomiques. Les erreurs restent génériques et les fichiers temporaires sont nettoyés."
        ),
        (
            "Fidélité, taille et limites fonctionnelles",
            "Les détections de tableaux restent heuristiques ; les cellules fusionnées, tableaux sans bordures "
            "et mises en page complexes doivent être validés sur des documents métier. Les indicateurs de "
            "qualité de compression ne sont pas une certification de fidélité visuelle. Les sorties DOCX/XLSX/"
            "PPTX peuvent nécessiter une correction manuelle."
        ),
        (
            "Windows autonome",
            "Le point d'entrée documenté reste BUILD-OPENPDF-WINDOWS.cmd à la racine du dépôt. Le pipeline "
            "prépare Python 3.12, les dépendances de l'application, les modèles OCR et Inno Setup lorsque "
            "nécessaire. Le manifeste runtime courant exige "
            f"{modules} modules distincts. Les exécutables ne sont pas déclarés signés Authenticode."
        ),
        (
            "Qualification de cette révision V548",
            _ci_summary(report)
        ),
        (
            "Limites de preuve",
            "La réussite des tests automatisés et des smoke tests Windows ne remplace pas une revue graphique "
            "humaine sous Windows. Le reçu runtime confirme le démarrage OCR, pas sa précision métier "
            "(accuracy_certified=false). Le précontrôle de chemin réduit les alias mais ne supprime pas une "
            "course TOCTOU après vérification ; les hard links ne sont pas distingués."
        ),
        (
            "Prochaine priorité",
            "Constituer un corpus Office annoté indépendamment pour mesurer la fidélité géométrique et visuelle "
            "des conversions, puis effectuer une qualification interactive humaine sous Windows. Préserver les "
            "preuves réelles, publier les limites avec chaque version et ne pas assimiler un schéma à une capture UI."
        ),
    ]


def build():
    # Imports are local so the pure formatting/qualification helpers stay testable
    # in minimal source-validation environments.
    from docx import Document
    from docx.shared import Inches
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
    )
    from xml.sax.saxutils import escape

    DOCS.mkdir(exist_ok=True)
    report = load_current_ci_report(ROOT)
    sections = build_sections(ROOT, report)
    module_count = required_module_count(ROOT)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    diagram = DOCS / "Architecture-V51.4-Pipeline.png"

    im = PILImage.new("RGB", (1400, 300), "white")
    draw = ImageDraw.Draw(im)
    labels = [
        ("PDF source", 25), ("Prévalidation", 295), ("Opération", 565),
        ("Vérification", 835), ("Publication", 1105),
    ]
    for label, x in labels:
        draw.rounded_rectangle(
            (x, 68, x + 220, 190), radius=18,
            outline="#176a7b", fill="#e6f3f5", width=4,
        )
        draw.text((x + 18, 118), label, fill="#153a4b")
        if x < 1100:
            draw.line((x + 220, 129, x + 250, 129), fill="#22627a", width=5)
            draw.polygon([(x + 250, 129), (x + 235, 121), (x + 235, 137)], fill="#22627a")
    draw.text((25, 235), "Refuser les alias de source et ne publier qu'après validation", fill="#a33333")
    im.save(diagram)

    doc = Document()
    doc.add_heading(TITLE, 0)
    doc.add_paragraph(f"Auteur : Abdelhalim Talbi | Généré : {generated}")
    doc.add_paragraph(
        "Version applicative : 51.4 | Jalon de développement : V548 | "
        + (f"commit {report['commit_sha']}" if report else "qualification CI de ce commit non vérifiée")
    )
    if report and report.get("pull_request"):
        doc.add_paragraph(
            f"PR #{report['pull_request']} : "
            f"https://github.com/{report['repository']}/pull/{report['pull_request']}"
        )
    doc.add_picture(str(diagram), width=Inches(6.2))
    doc.add_paragraph("Schéma d'architecture généré ; il ne s'agit pas d'une capture d'écran de l'application.")
    for heading, body in sections:
        if heading in ("Qualification de cette révision V548", "Limites de preuve"):
            doc.add_page_break()
        doc.add_heading(heading, level=1)
        for paragraph in body.split("\n"):
            if paragraph.strip():
                doc.add_paragraph(paragraph)
    capture = DOCS / "V51.4-GUI-Linux-Xvfb-REAL.png"
    if capture.is_file() and not capture.is_symlink():
        doc.add_heading("Capture réelle — interface Linux/Xvfb, pas Windows", level=1)
        doc.add_picture(str(capture), width=Inches(5.9))
    doc.save(DOCS / "OpenPDF-Studio-V51.4-Guide.docx")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="OpenPDFBody", parent=styles["BodyText"], leading=14, spaceAfter=7,
    ))
    story = [
        Paragraph(escape(TITLE), styles["Title"]),
        Spacer(1, 10),
        Paragraph(escape(f"Auteur : Abdelhalim Talbi | Généré : {generated}"), styles["Normal"]),
        Paragraph(escape(
            "Version applicative : 51.4 | Jalon V548 | "
            + (f"commit {report['commit_sha']}" if report else "qualification CI de ce commit non vérifiée")
        ), styles["Normal"]),
        Spacer(1, 12),
        Image(str(diagram), width=480, height=103),
        Paragraph(
            "Schéma d'architecture généré ; non capture de l'application.",
            styles["Italic"],
        ),
        Spacer(1, 12),
    ]
    if report and report.get("pull_request"):
        story.append(Paragraph(escape(
            f"PR #{report['pull_request']} : https://github.com/{report['repository']}/pull/{report['pull_request']}"
        ), styles["OpenPDFBody"]))
    for heading, body in sections:
        if heading in ("Qualification de cette révision V548", "Limites de preuve"):
            story.append(PageBreak())
        story.append(Paragraph(escape(heading), styles["Heading2"]))
        for paragraph in body.split("\n"):
            if paragraph.strip():
                story.append(Paragraph(escape(paragraph), styles["OpenPDFBody"]))
    if capture.is_file() and not capture.is_symlink():
        story += [
            PageBreak(),
            Paragraph("Capture réelle — interface Linux/Xvfb, pas Windows", styles["Heading2"]),
            Image(str(capture), width=480, height=310),
        ]
    pdf = DOCS / "OpenPDF-Studio-V51.4-Guide.pdf"
    SimpleDocTemplate(
        str(pdf), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42,
    ).build(story)
    return {"docx": DOCS / "OpenPDF-Studio-V51.4-Guide.docx", "pdf": pdf}


if __name__ == "__main__":
    build()
