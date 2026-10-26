"""Generate the V551 Word/PDF guide only from exact-commit Windows qualification.
Author: Abdelhalim Talbi.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = "04-Tests-et-Qualification/V551-CI-QUALIFICATION.json"
SCHEMA = "openpdf.v551.ci-qualification.v1"
WINDOWS_ONLY_TESTS = {
    "test_windows_publishes_by_handle_and_preserves_staging_name",
    "test_windows_existing_destination_is_never_replaced",
    "test_windows_junction_ancestor_is_rejected",
    "test_windows_dotdot_does_not_hide_junction",
    "test_windows_parent_swap_is_detected_without_redirect",
    "test_windows_staging_cannot_be_renamed_while_pinned",
}


def load_current_report(root=ROOT, expected_head_sha=None):
    path = Path(root) / REPORT
    if not path.is_file() or path.is_symlink():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    head = (
        expected_head_sha
        or os.environ.get("OPENPDF_HEAD_SHA", "").strip()
        or os.environ.get("GITHUB_SHA", "").strip()
    )
    if (
        not isinstance(report, dict)
        or report.get("schema") != SCHEMA
        or report.get("version") != "51.4"
        or report.get("milestone") != "V551"
        or report.get("qualified") is not True
        or not isinstance(report.get("commit_sha"), str)
        or len(report.get("commit_sha", "")) != 40
    ):
        return None
    if head and report.get("commit_sha") != head:
        return None
    page = report.get("page_order")
    if (
        not isinstance(page, dict)
        or page.get("head_sha") != report.get("commit_sha")
        or page.get("status") != "completed"
        or page.get("conclusion") != "success"
        or not page.get("url")
    ):
        return None
    tests = page.get("tests")
    if not isinstance(tests, dict) or set(tests) != {"ubuntu", "windows"}:
        return None
    ubuntu, windows = tests["ubuntu"], tests["windows"]
    if not isinstance(ubuntu, dict) or (
        ubuntu.get("expected") != 8
        or ubuntu.get("passed") != 2
        or ubuntu.get("skipped") != 6
        or ubuntu.get("failed") != 0
        or set(ubuntu.get("skipped_names", [])) != WINDOWS_ONLY_TESTS
        or ubuntu.get("conclusion") != "success"
    ):
        return None
    if not isinstance(windows, dict) or (
        windows.get("expected") != 8
        or windows.get("passed") != 8
        or windows.get("skipped") != 0
        or windows.get("failed") != 0
        or windows.get("skipped_names") != []
        or windows.get("conclusion") != "success"
    ):
        return None
    parent = report.get("parent_v550")
    if (
        not isinstance(parent, dict)
        or parent.get("qualified") is not True
        or parent.get("commit_sha") != report.get("commit_sha")
    ):
        return None
    capabilities = report.get("capabilities")
    limits = report.get("limits")
    if (
        not isinstance(capabilities, dict)
        or capabilities.get("windows_native_handle_relative_publication") is not True
        or capabilities.get("windows_path_based_fallback") is not False
        or not isinstance(limits, dict)
        or limits.get("full_windows_toctou_elimination") is not False
    ):
        return None
    return report


def build_sections(report):
    if report is None:
        evidence = (
            "NON QUALIFIÉ : aucun reçu V551 valide lié exactement au commit de génération. "
            "Les résultats de commits antérieurs ne sont pas réutilisés."
        )
    else:
        ubuntu = report["page_order"]["tests"]["ubuntu"]
        windows = report["page_order"]["tests"]["windows"]
        evidence = (
            "Commit qualifié : " + report["commit_sha"] + ". "
            "Exécution CI : " + report["page_order"]["url"] + ". "
            f"Ubuntu : {ubuntu['passed']}/{ubuntu['expected']} réussis, "
            f"{ubuntu['skipped']} ignorés pour les plateformes non applicables, {ubuntu['failed']} échec. "
            f"Windows Server runner : {windows['passed']}/{windows['expected']} réussis, "
            f"{windows['skipped']} ignorés, {windows['failed']} échec. "
            "La suite comprend la publication nominale, le non-écrasement, la jonction, "
            "le remplacement du parent et le maintien du handle du temporaire."
        )
    return [
        ("Résumé", "V551 remplace le repli Windows fondé sur les chemins du primitive de publication exclusive par un chemin natif basé sur des handles Windows lorsque celui-ci est pris en charge."),
        ("Détails d’implémentation", "Le parent de destination est ouvert composant par composant avec NtCreateFile, OBJ_DONT_REPARSE et FILE_OPEN_REPARSE_POINT. Les handles sont gardés ouverts pendant l'opération. Le fichier temporaire est ouvert sans reparse point et sans partage de suppression, synchronisé puis publié avec NtSetInformationFile/FileLinkInformation et ReplaceIfExists à faux. L'entrée publiée est rouverte relativement au handle du parent et son identité volume/fichier est comparée au handle source. Le chemin du parent est ensuite rouvert et comparé au handle épinglé."),
        ("Qualification liée au commit", evidence),
        ("Portée prise en charge", "Chemins absolus sur lecteur local avec lettre, répertoires ordinaires et système de fichiers acceptant les liens durs. Les chemins UNC, lecteurs réseau mappés, noms ambigus et segments '..' sont refusés. Les API natives ou systèmes de fichiers qui ne permettent pas l'opération échouent fermé."),
        ("Résistance aux courses", "Le test de course déplace le répertoire parent après l'ouverture de ses handles et vérifie que les octets ne sont pas redirigés vers un nouveau répertoire sous le nom initial. Le test du temporaire vérifie que le handle ouvert empêche le renommage pendant la publication. Une substitution détectée après publication provoque une erreur et la sortie ancrée est conservée pour revue ; aucune suppression aveugle n'est tentée."),
        ("Limites de sécurité", "Ces tests déterministes ne constituent pas un audit d'intrusion exhaustif. La qualification ne revendique pas l'élimination absolue de toutes les courses TOCTOU sur Windows, ne couvre pas les lecteurs réseau/UNC, ne certifie pas l'OCR métier, la fidélité visuelle Office, l'interface graphique par un humain ou la signature Authenticode."),
        ("Prochaine priorité", "Étendre la qualification aux variantes de système de fichiers et aux scénarios de concurrence réels, tout en gardant l'échec fermé sur les environnements non pris en charge. Étudier une primitive native de publication qui réduit les limites de l'API de lien dur selon le système de fichiers et documenter les résultats mesurés."),
    ]


def build(root=ROOT):
    root = Path(root).resolve()
    report = load_current_report(root)
    sections = build_sections(report)
    title = "OpenPDF Studio V51.4 — V551 : publication Windows par handles"
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out_docx = root / "05-Documentation" / "OpenPDF-Studio-V51.4-V551-Guide.docx"
    out_pdf = root / "05-Documentation" / "OpenPDF-Studio-V51.4-V551-Guide.pdf"

    from docx import Document
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph("Auteur : Abdelhalim Talbi")
    doc.add_paragraph("Généré : " + generated)
    doc.add_paragraph("Version applicative : 51.4 ; jalon de sécurité : V551.")
    if report:
        doc.add_paragraph("Commit qualifié : " + report["commit_sha"])
        if report.get("pull_request"):
            doc.add_paragraph("PR : https://github.com/" + report["repository"] + "/pull/" + str(report["pull_request"]))
        doc.add_paragraph("Exécution CI : " + report["page_order"]["url"])
    else:
        doc.add_paragraph("Qualification CI de cette génération : NON VÉRIFIÉE.")
    doc.add_paragraph("Le SVG V551 associé est un diagramme technique, pas une capture d’écran.")
    for heading, body in sections:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(body)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_docx)

    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="V551Body", parent=styles["BodyText"], leading=14, spaceAfter=8))
    flow = [
        Paragraph(escape(title), styles["Title"]),
        Spacer(1, 8),
        Paragraph(escape("Auteur : Abdelhalim Talbi | " + generated), styles["BodyText"]),
        Paragraph(escape("Version applicative 51.4 — jalon V551"), styles["BodyText"]),
        Spacer(1, 12),
    ]
    if report:
        rows = [
            ["Commit", report["commit_sha"]],
            ["Ubuntu", "2/8 PASS, 6 tests Windows-only ignorés"],
            ["Windows", "8/8 PASS, 0 ignoré, 0 échec"],
            ["CI", report["page_order"]["url"]],
        ]
        table = Table([[Paragraph(escape(str(cell)), styles["BodyText"]) for cell in row] for row in rows],
                      colWidths=[85, 390])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef5")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9fb3c8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.extend([table, Spacer(1, 12)])
    else:
        flow.append(Paragraph(escape("NON QUALIFIÉ : le reçu ne correspond pas exactement à cette révision."), styles["BodyText"]))
        flow.append(Spacer(1, 12))
    for heading, body in sections:
        flow.append(Paragraph(escape(heading), styles["Heading2"]))
        flow.append(Paragraph(escape(body), styles["V551Body"]))
    SimpleDocTemplate(str(out_pdf), pagesize=A4, title=title, author="Abdelhalim Talbi").build(flow)
    return {"qualified": report is not None, "docx": str(out_docx), "pdf": str(out_pdf)}


def main():
    result = build()
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
