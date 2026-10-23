"""Generate version-specific, evidence-honest Word/PDF guides. Abdelhalim Talbi."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
import json
import hashlib
from docx import Document
from docx.shared import Inches, Pt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
version=(ROOT/'VERSION.txt').read_text(encoding='utf-8').strip()
if version == '50.8':
    import generate_docs_v508
    generate_docs_v508.generate()
elif version == '50.7':
    import generate_docs_v507
    generate_docs_v507.generate()
    raise SystemExit(0)
if version == '50.2':
    import generate_v502_docs
    generate_v502_docs.make()
    raise SystemExit(0)
if version == '50.1':
    import generate_docs_v501
    generate_docs_v501.main()
    raise SystemExit(0)
if version == '50.0':
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V50.0-Guide.{ext}' for ext in ('docx', 'pdf')]
    required.extend([docs / 'Architecture-Extraction-V50.0.png',
                     docs / 'RELEASE-V50.0-QUALITE-ET-ROADMAP.md'])
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        import generate_docs_v500
        generate_docs_v500.main()
    raise SystemExit(0)
if version == '49.9':
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.9-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-Exclusions-V49.9.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v499
        generate_docs_v499.main()
    raise SystemExit(0)
if version == '49.8':
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.8-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-Selecteurs-V49.8.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v498
        generate_docs_v498.main()
    raise SystemExit(0)
if version == '49.7':
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.7-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-Reorganisation-V49.7.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v497
        generate_docs_v497.main()
    raise SystemExit(0)
if version == '49.6':
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.6-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-OOXML-V49.6.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v496
        generate_docs_v496.main()
    raise SystemExit(0)
if version == '49.5':
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.5-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-Archive-Source-V49.5.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v495
        generate_docs_v495.main()
    raise SystemExit(0)
if version == '49.4':
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.4-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-Archive-Source-V49.4.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v494
        generate_docs_v494.main()
    raise SystemExit(0)
if version == '49.3':
    # Keep the qualified, version-specific guide; avoid replacing measured
    # results with a generic placeholder during later packaging.
    docs = ROOT / '05-Documentation'
    expected = [docs / f'OpenPDF-Studio-V49.3-Guide.{ext}' for ext in ('docx', 'pdf')]
    expected.append(docs / 'Architecture-Archive-Source-V49.3.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        import generate_docs_v493
        generate_docs_v493.main()
    raise SystemExit(0)
if version == '49.2':
    import generate_docs_v492
    generate_docs_v492.main()
    raise SystemExit(0)
if version == '49.1':
    import generate_docs_v491
    generate_docs_v491.generate()
    raise SystemExit(0)
if version == '49.0':
    # V49.0-specific, evidence-derived guides; never overwrite with old templates.
    import generate_docs_v490
    raise SystemExit(0)
if version == '48.4':
    # Dedicated V48.4 guides; never replace actual evidence with generic templates.
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V48.4-{kind}.{ext}'
                for kind in ('Guide', 'Architecture-Qualification')
                for ext in ('docx', 'pdf')]
    required.extend([docs / 'Architecture-Fidelite-Texte-V48.4.png',
                     ROOT / '04-Tests-et-Qualification' / 'Preuves-V48.4' / 'functional-evidence.json'])
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('Documentation ou preuve V48.4 manquante')
    raise SystemExit(0)
if version == '48.3':
    # Dedicated V48.3 documentation, verified against actual Linux PDF evidence.
    required = [ROOT/'05-Documentation'/f'OpenPDF-Studio-V48.3-Architecture-Qualification.{ext}'
                for ext in ('docx', 'pdf')]
    required.extend(ROOT/'05-Documentation'/f'OpenPDF-Studio-V48.3-Guide.{ext}' for ext in ('docx', 'pdf'))
    required.append(ROOT/'05-Documentation/Architecture-Controle-Visuel-V48.3.png')
    required.append(ROOT/'04-Tests-et-Qualification/Preuves-V48.3/functional-evidence.json')
    if any(not path.is_file() or path.stat().st_size == 0 for path in required):
        raise FileNotFoundError('Documentation ou preuve V48.3 manquante')
    raise SystemExit(0)
if version == '48.2':
    # V48.2 documentation is evidence-specific; never replace it with generic
    # historical release templates when a build invokes this entrypoint.
    required = [ROOT/'05-Documentation'/f'OpenPDF-Studio-V48.2-Architecture-Qualification.{ext}'
                for ext in ('docx', 'pdf')]
    required.append(ROOT/'05-Documentation/Architecture-Libelles-PDF-V48.2.png')
    required.append(ROOT/'04-Tests-et-Qualification/Preuves-V48.2/real-functional-evidence.json')
    if any(not path.is_file() or path.stat().st_size == 0 for path in required):
        raise FileNotFoundError('Documentation ou preuve V48.2 manquante')
    raise SystemExit(0)
if version == '47.7':
    import generate_docs_v477
    generate_docs_v477.generate()
    raise SystemExit(0)
if version == '47.6':
    import generate_docs_v476  # V47.6-specific evidence and architecture
    raise SystemExit(0)
if version == '47.4':
    import generate_docs_v474
    generate_docs_v474.build()
    raise SystemExit(0)
if version == '47.3':
    import generate_docs_v473
    generate_docs_v473.build()
    raise SystemExit(0)
if version == '47.2':
    import generate_docs_v472  # V47.2-specific Windows build architecture and evidence
    generate_docs_v472.generate()
    raise SystemExit(0)
if version == '47.1':
    import generate_docs_v471  # evidence-specific Word/PDF V47.1
    raise SystemExit(0)
if version == '47.0':
    # V47.0 guides are authored and rendered from real Linux qualification.
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V47.0-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(docs / 'Architecture-Compression-V47.0.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('Documentation V47.0 ou schéma manquant')
    raise SystemExit(0)
if version == '46.7':
    # V46.7 has dedicated rendered Word/PDF and real Linux OCR-budget evidence.
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V46.7-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(docs / 'Architecture-OCR-V46.7.png')
    required.append(ROOT / '04-Tests-et-Qualification' / 'Preuves-V46.7' /
                    'qualification-ocr-budget-reelle.json')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.7-specific OCR evidence/documentation missing')
    raise SystemExit(0)
if version == '46.6':
    # Dedicated, visually verified OCR native-text retention documentation.
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V46.6-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(docs / 'Architecture-OCR-V46.6.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.6 OCR documentation missing')
    raise SystemExit(0)
if version == '46.5':
    import generate_docs_v465
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V46.5-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(docs / 'Architecture-OCR-V46.5.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.5 OCR documentation missing')
    raise SystemExit(0)
if version == '46.4':
    import generate_docs_v464  # dedicated, evidence-honest OCR smart documentation
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V46.4-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(docs / 'Architecture-OCR-V46.4.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.4 OCR smart documentation missing')
    raise SystemExit(0)
if version == '46.3':
    # Dedicated OCR fidelity documentation, already rendered and inspected.
    docs = ROOT / '05-Documentation'
    required = [docs / f'OpenPDF-Studio-V46.3-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(docs / 'Architecture-OCR-V46.3.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.3 OCR fidelity documentation missing')
    raise SystemExit(0)
if version == '46.2':
    import generate_docs_v462  # dedicated OCR documentation and real Linux proof
    required = [ROOT/'05-Documentation'/f'OpenPDF-Studio-V46.2-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(ROOT/'05-Documentation/Architecture-OCR-V46.2.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.2 OCR evidence-specific documentation missing')
    raise SystemExit(0)
if version == '46.0':
    # Dedicated version-specific documentation; never replace with a generic template.
    required = [ROOT/'05-Documentation'/f'OpenPDF-Studio-V46.0-{name}.{ext}'
                for name in ('Guide', 'Architecture-et-Qualification')
                for ext in ('docx', 'pdf')]
    required.append(ROOT/'05-Documentation/Architecture-Controle-DOCX-V46.0.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in required):
        raise FileNotFoundError('V46.0 evidence-specific documentation missing')
    raise SystemExit(0)
if version == '45.9':
    # V45.9 evidence-specific Word/PDF are already generated and visually checked.
    # Do not overwrite them with a generic historical release template.
    expected = [ROOT/'05-Documentation'/f'OpenPDF-Studio-V45.9-Architecture-et-Qualification.{ext}'
                for ext in ('docx', 'pdf')]
    expected.append(ROOT/'05-Documentation/Architecture-Controle-Office-V45.9.png')
    if any(not p.is_file() or p.stat().st_size == 0 for p in expected):
        raise FileNotFoundError('Missing V45.9-specific documentation')
    raise SystemExit(0)
if version == '45.8':
    import generate_docs_v458  # dedicated V45.8 guide and real test evidence when available
    raise SystemExit(0)
# V45.5 ships a dedicated, visually verified guide with real OCG test evidence.
# Do not replace it with generic historical release notes during packaging.
if version == '45.5':
    docs = ROOT / '05-Documentation'
    expected = [docs / 'OpenPDF-Studio-V45.5-Guide.docx',
                docs / 'OpenPDF-Studio-V45.5-Guide.pdf',
                docs / 'Architecture-Protection-Calques-V45.5.png']
    missing = [str(p) for p in expected if not p.is_file() or p.stat().st_size == 0]
    if missing:
        raise FileNotFoundError('Missing V45.5-specific evidence: ' + ', '.join(missing))
    raise SystemExit(0)
# V45.0 has an evidence-specific, reproducible guide with a real Linux screenshot.
# Do not overwrite it with generic legacy release notes.
if version == '45.4':
    import generate_docs_v454  # specific V45.4 guide and evidence; no generic substitution
    raise SystemExit(0)
if version == '45.3':
    import generate_docs_v453  # specific V45.3 guide; never replace with generic release notes
    raise SystemExit(0)
if version == '45.1':
    import generate_docs_v451  # evidence-specific V45.1 guide
    raise SystemExit(0)
if version == '45.0':
    import generate_docs_v450  # generates version-specific DOCX/PDF from bundled evidence
    raise SystemExit(0)
if not re.fullmatch(r'\d+\.\d+',version):raise ValueError('Invalid version')
major,minor=map(int,version.split('.'))
next_version=f'{major}.{minor+1}'
docs=ROOT/'05-Documentation';docs.mkdir(exist_ok=True)
release=docs/f'RELEASE-V{version}-QUALITE-ET-ROADMAP.md'
if not release.is_file():raise FileNotFoundError(f'Missing release notes: {release}')
notes=release.read_text(encoding='utf-8')
diagram=docs/f'Architecture-Packaging-V{version}.png'
from render_release_diagram import create_diagram
create_diagram(diagram, version)
compression_diagram=None
active_diagram=None
if (major, minor) >= (44, 0):
    from render_active_content_diagram_v440 import create_diagram as create_active_diagram
    active_diagram=docs/f'Architecture-Securite-PDF-V{version}.png'
    create_active_diagram(active_diagram)
if (major, minor) >= (44, 1):
    from render_security_preflight_v441 import create_diagram as create_preflight_diagram
    preflight_diagram=docs/f'Architecture-Prevalidation-V{version}.png'
    create_preflight_diagram(preflight_diagram, version=version)
else:
    preflight_diagram=None
uri_diagram=None
if (major, minor) >= (44, 2):
    from render_uri_policy_v442 import create_diagram as create_uri_diagram
    uri_diagram=docs/f'Architecture-URI-V{version}.png'
    create_uri_diagram(uri_diagram)
adaptive_diagram=None
if (major, minor) >= (44, 3):
    from render_adaptive_diagram_v443 import create_diagram as create_adaptive_diagram
    adaptive_diagram=docs/f'Architecture-Adaptatif-V{version}.png'
    create_adaptive_diagram(adaptive_diagram, version=version)
if version=='43.0':
    from render_compression_diagram_v430 import create_diagram as create_compression_diagram
    compression_diagram=docs/f'Architecture-Compression-V{version}.png'
    create_compression_diagram(compression_diagram)

def windows_automated_qualified():
    """Read and bind real Windows artifacts; never infer qualification from CI env."""
    binary=ROOT/'01-Application'/'binary'
    setup=binary/f'OpenPDF-Studio-V{version}-Setup.exe'
    portable=binary/f'OpenPDF-Studio-Portable-V{version}.exe'
    install=binary/f'windows-installation-v{version}.json'
    if not all(p.is_file() for p in (setup,portable,install)):
        return False
    try:
        with setup.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
        data=json.loads(install.read_text(encoding='utf-8-sig'))
        return (data.get('passed') is True and str(data.get('version'))==version
                and data.get('artifact_sha256')==sha
                and {'silent_install_pass','installed_launch_pass','silent_uninstall_pass'}.issubset(set(data.get('steps',[]))))
    except (OSError,ValueError,TypeError):
        return False

qualified=windows_automated_qualified()
status=('Tests Windows automatisés documentés ; recette graphique manuelle non effectuée.'
        if qualified else 'Candidat source ; aucune qualification Windows native de cette version.')

sections=[
 ('Périmètre et positionnement',
  'OpenPDF Studio est une application locale pour les opérations PDF. Les fonctions existantes couvrent fusion, découpage, extraction, réorganisation, compression, OCR optionnel et conversions textuelles vers DOCX, XLSX et PPTX. La fidélité visuelle des conversions éditables n’est pas garantie.'),
 ('Nouvelle architecture de livraison',
  'La V'+version+' remplace la copie indiscriminée des répertoires de compilation par un moteur de packaging sélectif. La vérification des preuves Windows précède la création de l’archive. Le ZIP est ensuite relu, chaque fichier est haché et comparé à son inventaire avant publication atomique.'),
 ('Procédure Windows en une commande',
  r'Depuis la racine du dépôt complet : 02-Compilation\BUILD-AND-PACKAGE-WINDOWS.cmd. Python 3.12 et Inno Setup 6 sont requis ; le script de build gère les dépendances Python et peut installer les prérequis via winget hors CI. En CI Windows, les prérequis sont installés par le workflow.'),
 ('Sécurité, confidentialité et intégrité',
  'Le packaging exclut les environnements virtuels, caches, répertoires de compilation, journaux et fichiers sensibles connus. Il refuse les chemins traversants, noms Windows réservés, doublons insensibles à la casse et liens symboliques. Un manifeste SHA-256 couvre chaque membre ; les exécutables et leurs rapports de qualification sont liés cryptographiquement.'),
 ('Mesure de référence (prototype V42.6)',
  'Un prototype de recomposition V42.6 a réduit une archive de 257 113 391 à 84 857 989 octets (environ 67 %). Cette mesure historique ne préjuge pas de la taille ni de la qualification de la V'+version+'. Le ZIP V'+version+' doit être mesuré après compilation Windows.'),
 ('Qualification et limites',
  'Les tests Python locaux utilisent des fixtures synthétiques clairement identifiées et un rejeu sur les vrais fichiers de la release V42.6. Statut Windows : '+status+' Aucune capture UI réelle V'+version+' n’est disponible. Le diagramme ci-dessous est un schéma d’architecture, pas une capture.'),
 ('Exploitation et dépannage',
  'En cas d’échec d’une étape, ne pas distribuer le ZIP candidat. Examiner les rapports dans 01-Application/binary, corriger l’anomalie, relancer le script CMD et vérifier les SHA-256. Une archive précédemment publiée est conservée en cas d’échec de la nouvelle génération.'),
 ('Feuille de route',
  'V'+next_version+' : benchmarks de compression sur gros PDF, réduction mémoire, amélioration de la progression et qualification Windows interactive des parcours OCR et conversion Office.'),
]

if (major, minor) >= (43, 6):
 sections[1] = ('Contrôle qualité de la compression avec perte',
  'Le profil images_balanced conserve le texte vectoriel et compare les rendus RGB de chaque page à 0,75x. '
  'Les mesures MAE (erreur absolue moyenne, 0-255) et proportion de pixels modifiés sont calculées sur un échantillonnage '
  'déterministe. Rejet avant publication si MAE dépasse 12/255 ou si plus de 35 % des pixels échantillonnés '
  'présentent une différence moyenne de canal supérieure à 24/255. Aucun saut silencieux de page.')
 sections[4] = ('Taille, qualité et limites des mesures',
  'Le gain en octets et en pourcentage est mesuré sur les fichiers réels. La MAE et la proportion de pixels '
  'modifiés sont des indicateurs échantillonnés, pas une certification SSIM/PSNR ni une garantie de fidélité. '
  'Un budget maximal de 12 millions de pixels rendus par page limite la mémoire ; une page trop grande est refusée. '
  'Les contrôles existants de texte, SHA-256 et publication exclusive restent actifs.')
 sections[5] = ('Qualification et preuves V'+version,
  'Quinze nouveaux tests fonctionnels couvrent le rendu, les modifications de couleur, la géométrie, la publication '
  'et le parcours UI de destination. Statut Windows : '+status+
  ' Les diagrammes sont des schémas, aucune capture réelle Windows V'+version+' n’est disponible.')
 sections[7] = ('Feuille de route',
  'Prochaine version : benchmarks de compression sur gros PDF, calibration des seuils, contrôle Windows natif '
  'de la conversion DOCX/XLSX/PPTX et vérification des flux OCR.')

if (major, minor) >= (43, 8):
 sections[1] = ('Fidélité locale renforcée — refus sans mesure',
  'V43.8 refuse une compression si aucune zone de la grille 12x12 ne possède le nombre minimal de pixels '
  'échantillonnés. Une MAE locale supérieure à 38/255 OU une fraction locale de pixels altérés supérieure '
  'à 65 % bloque la publication, en plus des critères globaux. Une mesure absente ne vaut jamais zéro.')
 sections[4] = ('Interprétation et limites des indicateurs',
  'Le rapport comprend MAE globale, fraction globale, MAE locale maximale et fraction locale maximale. '
  'Les seuils sont heuristiques et non calibrés sur corpus métier ; le rendu 0,75x et le pas 3 peuvent '
  'manquer des détails fins. Aucun résultat ne certifie la fidélité, la structure interactive ou les signatures.')
 sections[5] = ('Preuves et qualification V'+version,
  'Les six nouveaux tests de V43.8 vérifient la fraction locale, les paramètres invalides, le refus sans '
  'zone admissible et la non-publication des sorties rejetées. Les tests sont locaux et synthétiques. '
  'Statut Windows : '+status+' Aucune capture UI réelle V'+version+' n’est disponible.')

if (major, minor) >= (44, 0):
 sections[1] = ('V44.0 — refus des documents actifs et signés',
  'Avant publication, le moteur refuse les PDF dont les signatures déclarées, permissions de certification, '
  'actions automatiques, JavaScript, XFA ou actions de lien non prises en charge risqueraient d’être modifiés. '
  'Le contrôle s’applique à la source et au candidat, sans exécuter les actions PDF.')
 sections[4] = ('Politique conservatrice et limites',
  'Cette politique refuse certains documents légitimes et ne constitue ni une analyse antivirus ni une '
  'validation cryptographique de signature. Les liens URI ordinaires restent admis. '
  'Les contrôles visuels restent échantillonnés et ne certifient pas la fidélité.')
 sections[5] = ('Preuves V'+version,
  'Les tests PyMuPDF utilisent des PDF synthétiques contenant des actions automatiques, des signatures déclarées '
  'et des liens URI. Ils contrôlent le refus, l’absence de publication et la conservation des liens autorisés. '
  'Statut Windows : '+status+' Aucune capture réelle V'+version+' disponible.')
 sections[7] = ('Feuille de route',
  'Intégrer la branche GitHub, obtenir une qualification Windows native, étendre la préservation des structures '
  'PDF avancées, puis mesurer OCR et conversions Office sur un corpus représentatif.')

if (major, minor) >= (44, 1):
 sections[1] = ('V44.1 - Chiffrement et actions PDF chaînées',
  'Correction vérifiée : MuPDF peut ouvrir un PDF AES-256 avec mot de passe utilisateur vide '
  'sans activer needs_pass ni is_encrypted. Le garde-fou inspecte désormais /Encrypt dans '
  'le trailer parsé et refuse sa réécriture. Les actions URI suivies de /Next, les actions '
  'Named et les actions inconnues sont également rejetées. Les liens URI simples restent admis.')
 sections[4] = ('Contrôles et limites de sécurité',
  'Prévalidation de la source avant toute compression ; vérification supplémentaire de la '
  'source et du candidat avant publication exclusive. Le contrôle ne constitue ni un antivirus '
  'ni une validation cryptographique des signatures et peut refuser des PDF légitimes.')
 sections[5] = ('Preuves de qualification V44.1',
  'Neuf nouveaux tests fonctionnels sur de vrais PDF synthétiques, 279 tests locaux réussis '
  'au total sous Linux/Python 3.13/PyMuPDF 1.26.7. Compilation Windows V44.1, installateur '
  'et recette graphique : non exécutés. Aucune capture UI réelle V44.1. '+status)
 sections[7] = ('Priorité du prochain cycle',
  'Réconcilier le candidat source avec GitHub, publier le code, ouvrir une PR et obtenir une '
  'qualification Windows réelle. Mesurer ensuite les coûts de prévalidation sur gros PDF.')

if (major, minor) >= (44, 2):
 sections[1] = ('V44.2 - Politique explicite pour les actions URI PDF',
  'Le garde-fou analyse les chaînes URI décodées par le parseur PDF, avant compression. '
  'Seuls http, https et mailto sont admis, avec un hôte obligatoire pour http(s). '
  'Les chaînes vides ou de plus de 2048 caractères, les caractères de contrôle Unicode, '
  'les séparateurs blancs, les antislashs, les schémas inconnus, les URI sans hôte '
  'et les actions chaînées sont rejetés. Les liens internes GoTo restent admis.')
 sections[4] = ('Limites et compatibilité V44.2',
  'Le filtrage conservateur peut refuser des liens métier légitimes utilisant ftp, '
  'file, tel ou des schémas personnalisés. Il ne valide pas la destination distante, '
  'ne garantit pas la sûreté des URL autorisées et ne constitue pas un antivirus. '
  'La fidélité de rendu et des conversions Office reste à qualifier sur corpus réel.')
 sections[5] = ('Qualification V44.2 - preuves et périmètre',
  'Les nouveaux tests créent de vrais PDF synthétiques PyMuPDF et vérifient les URI '
  'autorisées, les schémas refusés, les échappements PDF, les contrôles Unicode, '
  'la prévalidation avant moteur et la non-publication. Les résultats complets figurent '
  'dans 04-Tests-et-Qualification. Qualification Windows native : non exécutée. '
  'Aucune capture UI réelle Windows V44.2 n’a été produite. '+status)
 sections[7] = ('Prochaine priorité V44.3',
  'Réconcilier les sources V43.5 à V44.2 avec la branche distante, publier une PR '
  'et qualifier les binaires Windows, puis mesurer la fidélité et les performances '
  'sur un corpus documentaire représentatif.')


if (major, minor) >= (44, 3):
 sections[1] = ('V44.3 - Compression JPEG adaptative contrôlée',
  'Nouveau profil images_adaptive : trois essais explicites JPEG 55, 70 et 85 à 150 dpi. '
  'Chaque candidat est évalué avant sélection : intégrité SHA-256 de la source, texte extrait, '
  'comparaison visuelle globale et locale, et conservation des structures PDF. '
  'Seule la plus petite sortie validée et strictement plus petite que la source est publiée.')
 sections[4] = ('Coûts, seuils et politique de refus',
  'Trois réencodages et contrôles de qualité peuvent accroître fortement le temps de traitement. '
  'Aucun gain signifie aucune publication ; aucun candidat conforme entraîne une erreur explicite. '
  'Les seuils de rendu sont heuristiques, sans garantie de fidélité parfaite. '
  'La sélection est bornée à trois essais et conserve le refus des PDF actifs/chiffrés.')
 sections[5] = ('Qualification V44.3 - preuves réelles et limites',
  'Dix nouveaux tests locaux V44.3 vérifient sélection, rejet, intégrité, absence de gain, '
  'nettoyage et consentement UI. Le benchmark est un PDF de dégradé synthétique, '
  'et non un document client. Aucune compilation ou capture réelle Windows V44.3. '+status)
 sections[7] = ('Priorité suivante',
  'Réconcilier les sources cumulatives V43.5-V44.3 avec la branche GitHub, obtenir une PR et '
  'qualifier les exécutables Windows. Étendre ensuite le corpus PDF réel, les mesures de '
  'finesse de caractères et les conversions Office éditables.')

if (major, minor) >= (44, 4):
 sections[1] = ('V44.4 — Compression adaptative résiliente et économique',
  'Le moteur essaie trois qualités JPEG bornées et conserve uniquement les candidats plus petits que la source. '
  'Un candidat de taille supérieure est déclaré sans gain et ne déclenche aucun rendu, extraction de texte ni '
  'inspection des structures. Une erreur récupérable de réencodage est journalisée et le moteur tente la '
  'qualité suivante. Les modifications de source restent des erreurs fatales même si le compresseur échoue.')
 sections[4] = ('Sécurité et performances — invariants vérifiés',
  'La vérification SHA-256 de la source est exécutée avant et après chaque tentative, y compris en cas '
  'd’erreur du compresseur. La sortie n’est jamais publiée si aucun candidat conforme et plus petit '
  'n’est disponible. Les essais temporaires sont supprimés. Les seuils de qualité sont heuristiques '
  'et ne certifient pas une fidélité parfaite. La durée et la mémoire doivent être mesurées sur un corpus réel.')
 sections[5] = ('Qualification V44.4 — limites de preuve',
  'Neuf nouveaux tests fonctionnels PyMuPDF synthétiques couvrent les pannes JPEG partielles et totales, '
  'la non-publication, le court-circuit des validations coûteuses sur candidats trop volumineux, '
  'la mutation concurrente de la source et la conservation des destinations existantes. '
  'La suite complète est documentée dans V44.4-LOCAL-QUALIFICATION.json. '
  'Aucune compilation ni capture réelle Windows V44.4. '+status)
 sections[7] = ('Prochaine priorité',
  'Réconcilier les sources locales V43.5–V44.4 avec le dépôt GitHub, ouvrir une PR intégrable et '
  'qualifier la CI Windows. Mesurer le coût de compression sur PDF réels multi-pages et améliorer '
  'la fidélité des conversions Word/Excel/PowerPoint éditables.')

if (major, minor) >= (44, 5):
 sections[1] = ('V44.5 — Géométrie et apparence des annotations PDF',
  'Le garde-fou compare maintenant les bordures (largeur, pointillés et style), les sommets, '
  'les terminaisons de ligne et le mode de fusion. Une différence bloque la publication, '
  'même lorsque les métadonnées descriptives et les rectangles des annotations sont inchangés.')
 sections[4] = ('Invariants, limites et sécurité',
  'La comparaison se fonde sur les propriétés PyMuPDF et ne constitue pas une preuve de '
  'fidélité parfaite ni un audit de tous les dictionnaires PDF. Les signatures restent refusées. '
  'Les fichiers existants ne sont pas écrasés et les fichiers temporaires rejetés sont nettoyés.')
 sections[5] = ('Preuves et qualification V44.5',
  '316 tests Python locaux réussis, dont 5 nouveaux tests V44.5 utilisant de véritables PDF '
  'synthétiques. Compilation statique réussie. Aucune compilation, installation, CI ou '
  'capture réelle Windows V44.5. '+status)
 sections[7] = ('Priorité du prochain cycle',
  'Réconcilier V43.5–V44.5 avec GitHub, publier une PR, obtenir une CI Windows native, '
  'puis mesurer les performances et la fidélité des conversions Office éditables.')

if (major, minor) >= (44, 6):
 sections[1] = ('V44.6 — Contrôle SHA-256 du découpage transactionnel',
  'Le service split_transaction prend un instantané SHA-256 et une identité stable du PDF source '
  'avant de préparer les lots. Il vérifie la source avant la première publication et après la dernière. '
  'Une modification de taille constante avec mtime restauré, un changement d’inode ou une suppression '
  'provoque le rejet. Les liens appartenant à la transaction sont supprimés au rollback sans écraser '
  'les remplacements étrangers.')
 sections[4] = ('Limites du modèle transactionnel',
  'Le découpage publie plusieurs fichiers via des liens exclusifs, sans atomicité globale. '
  'Le SHA-256 ne verrouille pas le PDF source ; une modification juste après la dernière vérification '
  'reste possible. La récupération après crash requiert une réservation coopérative du dossier. '
  'Aucune garantie de sécurité antivirus ou de fidélité des conversions Office n’est impliquée.')
 sections[5] = ('Preuves et qualification V44.6',
  '322 tests Python locaux réussis sous Linux/Python 3.13/PyMuPDF 1.26.7, dont 6 nouveaux tests '
  'sur de vrais PDF synthétiques. Compilation statique réussie. Le commit GitHub 80462ba ne '
  'contient que le module d’empreinte ; l’intégration du service et les tests restent bloqués '
  'à la publication. CI Windows V44.6, installateur et capture UI réelle : non exécutés. '+status)
 sections[7] = ('Prochaine priorité',
  'Terminer la publication du service et des tests sur feature/v44.6-split-sha256-commit-gate, '
  'ouvrir une PR vers develop, obtenir une CI Windows native puis réconcilier les candidats cumulés '
  'V43.5 à V44.5 sans écraser les modifications distantes.')

title=f'OpenPDF Studio V{version} — Guide technique et utilisateur'
doc=Document()
doc.styles['Normal'].font.size=Pt(9)
doc.styles['Normal'].paragraph_format.space_after=Pt(4)
sec=doc.sections[0];sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.60)
doc.add_heading(title,0)
doc.add_paragraph('Auteur : Abdelhalim Talbi')
doc.add_paragraph('Statut : '+status)
for heading,body in sections:
 doc.add_heading(heading,level=1)
 doc.add_paragraph(body)
if adaptive_diagram:
 doc.add_heading(f'Circuit adaptatif V{version} - schéma conceptuel',level=1)
 doc.add_picture(str(adaptive_diagram),width=Inches(6.2))
 doc.add_paragraph('Diagramme de conception ; non capture UI réelle.')
if compression_diagram:
 doc.add_heading('Schéma du contrôle de compression V43.0',level=1)
 doc.add_picture(str(compression_diagram),width=Inches(6.2))
 doc.add_paragraph('Schéma de conception : pas une capture d’écran réelle.')
if active_diagram:
 doc.add_heading('Schéma conceptuel du garde-fou V44.0',level=1)
 doc.add_picture(str(active_diagram),width=Inches(6.2))
 doc.add_paragraph('Schéma de conception ; aucune capture UI réelle.')
if preflight_diagram:
 doc.add_heading(f'Prévalidation V{version} avant compression',level=1)
 doc.add_picture(str(preflight_diagram),width=Inches(6.2))
 doc.add_paragraph('Schéma conceptuel ; non capture d’interface.')
if uri_diagram:
 doc.add_heading('Politique URI V44.2 - schéma conceptuel',level=1)
 doc.add_picture(str(uri_diagram),width=Inches(6.2))
 doc.add_paragraph('Diagramme de conception, non capture UI réelle.')
if (major, minor) >= (44, 5):
 doc.add_heading('Préservation des annotations — schéma conceptuel V44.5',level=1)
 doc.add_picture(str(docs/'Architecture-Annotations-V44.5.png'),width=Inches(6.2))
 doc.add_paragraph('Diagramme de conception ; non capture réelle de l’interface.')
if (major, minor) >= (44, 6):
 doc.add_heading('Découpage transactionnel SHA-256 V44.6 — schéma conceptuel',level=1)
 doc.add_picture(str(docs/'Architecture-Decoupage-SHA256-V44.6.png'),width=Inches(6.2))
 doc.add_paragraph('Diagramme de conception ; non capture réelle de l’interface Windows.')
doc.add_heading('Schéma d’architecture de livraison',level=1)
doc.add_picture(str(diagram),width=Inches(6.2))
doc.add_paragraph('Schéma technique explicatif, non capture de l’interface utilisateur.')
if version == '51.1':
 doc.add_heading('Pipeline OCR → Office V51.1',level=1)
 doc.add_picture(str(docs/'Architecture-OCR-Office-V51.1.png'),width=Inches(6.2))
 doc.add_paragraph('Schéma conceptuel, non capture Windows réelle.')
doc.add_heading('Contrôles de qualification',level=1)
table=doc.add_table(rows=1,cols=2);table.style='Light Shading Accent 1'
for i,head in enumerate(('Contrôle','État constaté')):table.rows[0].cells[i].text=head
for a,b in [('Tests packaging locaux','Voir rapport local et CI ; fixtures synthétiques'),('Tests statiques orchestration','Voir CI ; contrôles de contrat'),('Tests fonctionnels sélectionnés','Voir logs du workflow Windows'),('Mesure historique V42.6','Prototype seulement, non V'+version),('Compilation Windows V'+version,'Automatisée : PASS' if qualified else 'Non exécutée'),('Recette UI Windows V'+version,'Non exécutée')]:
 row=table.add_row();row.cells[0].text=a;row.cells[1].text=b
doc.add_heading('Notes de version détaillées',level=1)
for line in notes.splitlines():
 if not line.strip():continue
 if line.startswith('## '):doc.add_heading(line[3:],level=2)
 elif line.startswith('# '):doc.add_heading(line[2:],level=1)
 else:doc.add_paragraph(line.replace('**','').replace('`',''))
word=docs/f'OpenPDF-Studio-V{version}-Guide.docx'
doc.save(word)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='GuideBody',parent=styles['BodyText'],leading=15,spaceAfter=8))
story=[Paragraph(escape(title),styles['Title']),Spacer(1,10),Paragraph('Auteur : Abdelhalim Talbi',styles['Normal']),Paragraph(escape(status),styles['Normal']),Spacer(1,14)]
for heading,body in sections:
 story.append(Paragraph(escape(heading),styles['Heading2']))
 story.append(Paragraph(escape(body),styles['GuideBody']))
story.append(Spacer(1,20))
if adaptive_diagram:
 story.append(Paragraph('Circuit de compression adaptative V44.3',styles['Heading2']))
 story.append(Image(str(adaptive_diagram),width=480,height=133))
 story.append(Paragraph('Schéma de conception ; non capture UI.',styles['Normal']))
 story.append(Spacer(1,15))
if compression_diagram:
 story.append(Paragraph('Contrôle de compression V43.0',styles['Heading2']))
 story.append(Image(str(compression_diagram),width=480,height=175))
 story.append(Paragraph('Diagramme explicatif, non capture UI.',styles['Normal']))
 story.append(Spacer(1,15))
if active_diagram:
 story.append(Paragraph('Garde-fou de compression V44.0',styles['Heading2']))
 story.append(Image(str(active_diagram),width=480,height=123))
 story.append(Paragraph('Schéma de conception ; non capture UI.',styles['Normal']))
 story.append(Spacer(1,15))
if preflight_diagram:
 story.append(Paragraph(f'Prévalidation V{version} avant compression',styles['Heading2']))
 story.append(Image(str(preflight_diagram),width=480,height=125))
 story.append(Paragraph('Schéma conceptuel, non capture UI.',styles['Normal']))
 story.append(Spacer(1,15))
if uri_diagram:
 story.append(Paragraph('Politique URI V44.2 - schéma conceptuel',styles['Heading2']))
 story.append(Image(str(uri_diagram),width=480,height=125))
 story.append(Paragraph('Diagramme de conception, non capture UI.',styles['Normal']))
 story.append(Spacer(1,15))
if (major, minor) >= (44, 5):
 story.append(Paragraph('Préservation des annotations V44.5 — schéma conceptuel',styles['Heading2']))
 story.append(Image(str(docs/'Architecture-Annotations-V44.5.png'),width=480,height=157))
 story.append(Paragraph('Diagramme de conception ; non capture réelle.',styles['Normal']))
if (major, minor) >= (44, 6):
 story.append(Paragraph('Découpage transactionnel SHA-256 V44.6 — schéma conceptuel',styles['Heading2']))
 story.append(Image(str(docs/'Architecture-Decoupage-SHA256-V44.6.png'),width=480,height=189))
 story.append(Paragraph('Diagramme de conception ; non capture réelle de l’interface Windows.',styles['Normal']))
 story.append(Spacer(1,15))
story.append(Paragraph('Schéma d’architecture de livraison',styles['Heading2']))
story.append(Image(str(diagram),width=480,height=185))
story.append(Paragraph('Schéma technique, non capture UI.',styles['Normal']))
if version == '51.1':
 story.append(Paragraph('Pipeline OCR → Office V51.1',styles['Heading2']))
 story.append(Image(str(docs/'Architecture-OCR-Office-V51.1.png'),width=480,height=144))
 story.append(Paragraph('Schéma conceptuel, non capture Windows réelle.',styles['Normal']))
story.append(Spacer(1,15))
rows=[['Contrôle','État constaté'],['Tests packaging locaux','Voir CI (fixtures synthétiques)'],['Tests statiques','Voir CI'],['Tests sélectionnés','Voir logs GitHub Actions'],['Mesure historique V42.6','Prototype uniquement'],['Windows V'+version,'Automatisé : PASS' if qualified else 'Non exécuté'],['UI Windows V'+version,'Non exécutée']]
t=Table(rows,colWidths=[190,285]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceafa')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#a0b3c7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(KeepTogether([Paragraph('Contrôles de qualification',styles['Heading2']),t]))
story.append(Spacer(1,16))
story.append(Paragraph('Notes de version détaillées',styles['Heading1']))
for line in notes.splitlines():
 line=line.strip()
 if not line:continue
 if line.startswith('# '):continue
 if line.startswith('## '):story.append(Paragraph(escape(line[3:]),styles['Heading2']))
 elif line.startswith('```'):continue
 else:
  line=line.replace('**','').replace('`','')
  story.append(Paragraph(escape(line),styles['GuideBody']))
pdf=docs/f'OpenPDF-Studio-V{version}-Guide.pdf'
SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=45,bottomMargin=45).build(story)
print('Generated:',word,pdf)
