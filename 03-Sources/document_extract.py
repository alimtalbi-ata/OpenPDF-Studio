"""OpenPDF Studio R23 — real PDF/DOCX text-box extraction. Abdelhalim Talbi.

DOCX has no stable page coordinates without a layout engine: returns a single
logical page with synthetic block positions, explicitly marked as such.
"""
from __future__ import annotations
from pathlib import Path
import math
import shutil
import subprocess
import tempfile

MAX_BYTES = 50 * 1024 * 1024
MAX_PAGES = 1000

class ExtractionError(ValueError):
    pass

def _validate(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_file():
        raise ExtractionError(f'File not found: {p}')
    if p.stat().st_size > MAX_BYTES:
        raise ExtractionError('Input file exceeds 50 MiB')
    return p

def extract_pdf(path: str | Path) -> dict:
    """Extract text spans with real PDF coordinates using PyMuPDF; no OCR."""
    p = _validate(path)
    try:
        import fitz
    except ImportError as exc:
        raise ExtractionError('PyMuPDF is required: pip install pymupdf') from exc
    pages = []
    try:
        with fitz.open(str(p)) as doc:
            if doc.needs_pass:
                raise ExtractionError('Encrypted PDF requires an unlocked input')
            if len(doc) > MAX_PAGES:
                raise ExtractionError('PDF exceeds 1000 pages')
            for page in doc:
                blocks = []
                for block in page.get_text('dict').get('blocks', []):
                    if 'lines' not in block:
                        continue
                    for line in block['lines']:
                        for span in line['spans']:
                            value = span['text'].strip()
                            if not value:
                                continue
                            x0,y0,x1,y1 = map(float, span['bbox'])
                            if not all(map(math.isfinite,(x0,y0,x1,y1))) or x1<=x0 or y1<=y0:
                                continue
                            blocks.append({'text': value,'box':{'x':x0,'y':y0,'w':x1-x0,'h':y1-y0}})
                pages.append({'width':float(page.rect.width),'height':float(page.rect.height),'blocks':blocks})
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f'Cannot extract PDF: {exc}') from exc
    return {'format':'pdf','geometry':'native_pdf','pages':pages,'warnings':(['No extractable text; scanned pages require OCR'] if pages and not any(p['blocks'] for p in pages) else [])}

def extract_docx(path: str | Path) -> dict:
    """Extract text from DOCX; coordinates are synthetic, not layout faithful."""
    p = _validate(path)
    try:
        from docx import Document
    except ImportError as exc:
        raise ExtractionError('python-docx required: pip install python-docx') from exc
    try:
        doc = Document(str(p))
        # Preserve body order (paragraphs/tables) using the document XML body.
        from docx.oxml.ns import qn
        texts=[]
        for child in doc.element.body.iterchildren():
            if child.tag == qn('w:p'):
                txt=''.join(t.text or '' for t in child.iter(qn('w:t'))).strip()
                if txt:texts.append(txt)
            elif child.tag == qn('w:tbl'):
                for tr in child.iter(qn('w:tr')):
                    for tc in tr.iter(qn('w:tc')):
                        txt=' '.join(t.text or '' for t in tc.iter(qn('w:t'))).strip()
                        if txt:texts.append(txt)
        if len(texts)>100000:raise ExtractionError('DOCX has too many text blocks')
        height=max(800, 25*(len(texts)+2))
        blocks=[{'text':t,'box':{'x':30,'y':20+i*25,'w':min(500,max(20,len(t)*6)),'h':18}} for i,t in enumerate(texts)]
        return {'format':'docx','geometry':'synthetic_logical_order','pages':[{'width':600,'height':height,'blocks':blocks}], 'warnings':['DOCX page positions are synthetic; layout/movement scores are not reliable','DOCX content is represented as one logical page']}
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f'Cannot extract DOCX: {exc}') from exc

def extract_pptx(path: str | Path) -> dict:
    """Extract slide text with shape geometry (EMU to points); not a rendered slide."""
    p = _validate(path)
    try:
        from pptx import Presentation
        from pptx.util import Pt
    except ImportError as exc:
        raise ExtractionError('python-pptx required: pip install python-pptx') from exc
    try:
        presentation = Presentation(str(p))
        if len(presentation.slides) > MAX_PAGES:
            raise ExtractionError('PPTX exceeds 1000 slides')
        scale = 12700.0  # 1 point = 12700 EMU
        width, height = presentation.slide_width/scale, presentation.slide_height/scale
        pages=[]
        for slide in presentation.slides:
            blocks=[]
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                content = shape.text.strip()
                if not content:
                    continue
                x,y,w,h=(float(v)/scale for v in (shape.left,shape.top,shape.width,shape.height))
                if w<=0 or h<=0:continue
                blocks.append({'text':content,'box':{'x':x,'y':y,'w':w,'h':h}})
            pages.append({'width':width,'height':height,'blocks':blocks})
        return {'format':'pptx','geometry':'pptx_shape_bounds','pages':pages,'warnings':['PPTX coordinates are text-shape bounds, not exact glyph positions; text overflow, fonts and rendering are not evaluated']}
    except ExtractionError:raise
    except Exception as exc:raise ExtractionError(f'Cannot extract PPTX: {exc}') from exc

def extract_xlsx(path: str | Path) -> dict:
    """Extract cached/formula cell text in worksheet order; synthetic geometry."""
    p = _validate(path)
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ExtractionError('openpyxl required: pip install openpyxl') from exc
    try:
        wb=load_workbook(str(p),read_only=True,data_only=False)
        if len(wb.worksheets)>MAX_PAGES:raise ExtractionError('XLSX exceeds 1000 worksheets')
        pages=[]
        for ws in wb.worksheets:
            blocks=[]
            count=0
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value is None:continue
                    count+=1
                    if count>100000:raise ExtractionError('XLSX exceeds 100000 nonempty cells per sheet')
                    value=str(cell.value)
                    blocks.append({'text':value,'box':{'x':20+(cell.column-1)*110,'y':20+(cell.row-1)*25,'w':105,'h':20},'cell':cell.coordinate})
            maxcol=max((b['box']['x']+b['box']['w'] for b in blocks),default=600)
            maxrow=max((b['box']['y']+b['box']['h'] for b in blocks),default=800)
            pages.append({'width':max(600,maxcol+20),'height':max(800,maxrow+20),'blocks':blocks})
        wb.close()
        return {'format':'xlsx','geometry':'synthetic_grid','pages':pages,'warnings':['XLSX geometry is synthetic: worksheet cells are not print pages','Formulas are extracted as expressions; displayed/cached values and charts are not compared']}
    except ExtractionError:raise
    except Exception as exc:raise ExtractionError(f'Cannot extract XLSX: {exc}') from exc


def render_office_to_pdf(path: str | Path, *, timeout: float = 45,
                         executable: str = "libreoffice") -> dict:
    """Opt-in LibreOffice rendering to PDF, then extract true PDF text boxes."""
    p = _validate(path)
    if p.suffix.lower() not in (".docx", ".pptx", ".xlsx"):
        raise ExtractionError("Office rendering supports DOCX, PPTX, XLSX only")
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 300:
        raise ExtractionError("Render timeout must be within (0, 300] seconds")
    binary = shutil.which(executable)
    if not binary:
        raise ExtractionError("LibreOffice executable not found; no silent fallback")
    with tempfile.TemporaryDirectory(prefix="openpdf-render-") as root:
        work = Path(root)
        profile = work / "profile"
        output = work / "output"
        output.mkdir()
        try:
            run = subprocess.run([
                binary, "-env:UserInstallation=" + profile.as_uri(),
                "--headless", "--convert-to", "pdf", "--outdir", str(output),
                str(p.resolve()),
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
               timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ExtractionError("LibreOffice rendering timed out") from exc
        except OSError as exc:
            raise ExtractionError(f"LibreOffice could not start: {exc}") from exc
        pdf = output / (p.stem + ".pdf")
        if run.returncode != 0 or not pdf.is_file() or pdf.stat().st_size == 0:
            raise ExtractionError("LibreOffice conversion failed; no synthetic fallback")
        result = extract_pdf(pdf)
    result.update(format=p.suffix.lower().lstrip("."),
                  geometry="libreoffice_rendered_pdf",
                  warnings=result["warnings"] + [
                      "Layout is from LibreOffice PDF rendering, not Microsoft Office",
                      "Rendering depends on available fonts, print settings and LibreOffice version",
                  ])
    return result

def extract_document(path: str | Path) -> dict:
    ext=Path(path).suffix.lower()
    if ext=='.pdf':return extract_pdf(path)
    if ext=='.docx':return extract_docx(path)
    if ext=='.pptx':return extract_pptx(path)
    if ext=='.xlsx':return extract_xlsx(path)
    raise ExtractionError('Supported formats: PDF, DOCX, PPTX, XLSX')

def compare_documents(source: str | Path, target: str | Path, *, timeout:float=30, render_office: bool=False, render_timeout:float=45) -> dict:
    """Run the R22 engine; preserve explicit geometry reliability metadata."""
    from python_bridge import run_diagnostic
    a,b=(render_office_to_pdf(source, timeout=render_timeout) if render_office and Path(source).suffix.lower() != '.pdf' else extract_document(source)),(render_office_to_pdf(target, timeout=render_timeout) if render_office and Path(target).suffix.lower() != '.pdf' else extract_document(target))
    from multipage_audit import audit_multipage
    page_audit = audit_multipage(a['pages'], b['pages'])
    from boundary_audit import audit_page_boundaries
    boundary_audit = {'source':audit_page_boundaries(a['pages']), 'target':audit_page_boundaries(b['pages'])}
    result=run_diagnostic(a['pages'],b['pages'],timeout=timeout)
    table_structure = None
    if Path(source).suffix.lower() in ('.docx', '.xlsx') and Path(target).suffix.lower() in ('.docx', '.xlsx'):
        from table_structure_audit import compare_table_structures
        table_structure = compare_table_structures(source, target)
    pdf_office_tables = None
    if {Path(source).suffix.lower(), Path(target).suffix.lower()} in ({'.pdf', '.docx'}, {'.pdf', '.xlsx'}):
        from pdf_table_audit import compare_pdf_office_tables
        pdf_office_tables = compare_pdf_office_tables(source, target)
    return {'pdf_office_table_audit':pdf_office_tables,'table_structure_audit':table_structure,'source':{'format':a['format'],'geometry':a['geometry']},'target':{'format':b['format'],'geometry':b['geometry']},'warnings':a['warnings']+b['warnings'],'multipage_audit':page_audit,'boundary_audit':boundary_audit,'layout_comparable':a['geometry'] in ('native_pdf','libreoffice_rendered_pdf') and b['geometry'] in ('native_pdf','libreoffice_rendered_pdf'),'diagnostic':result}
