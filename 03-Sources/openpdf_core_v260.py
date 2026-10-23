"""OpenPDF Studio V26.0: offline PDF operations. Author: Abdelhalim Talbi."""
from pathlib import Path
import fitz

class PDFOperationError(ValueError): pass

def _inputs(paths):
    paths=[Path(p) for p in paths]
    if not paths or any(not p.is_file() or p.suffix.lower()!='.pdf' for p in paths):
        raise PDFOperationError('Sélectionnez des fichiers PDF existants.')
    return paths

def _output(output, sources):
    output=Path(output)
    if output.suffix.lower()!='.pdf': raise PDFOperationError('Le fichier de sortie doit être un PDF.')
    if output.resolve() in {p.resolve() for p in sources}: raise PDFOperationError('La sortie ne peut pas écraser un document source.')
    output.parent.mkdir(parents=True,exist_ok=True)
    return output

def merge_pdfs(paths, output):
    paths=_inputs(paths); output=_output(output,paths)
    with fitz.open() as result:
        for path in paths:
            with fitz.open(path) as doc:
                if doc.needs_pass: raise PDFOperationError(f'PDF protégé : {path.name}')
                result.insert_pdf(doc)
        if not result.page_count: raise PDFOperationError('Aucune page à fusionner.')
        result.save(output,garbage=4,deflate=True)
    return [output]

def split_pdf(source, folder, mode='pages', chunk_size=1):
    source=_inputs([source])[0]; folder=Path(folder)
    if mode not in ('pages','chunks'): raise PDFOperationError('Mode de découpage invalide.')
    if not isinstance(chunk_size,int) or chunk_size<1: raise PDFOperationError('Taille de lot invalide.')
    folder.mkdir(parents=True,exist_ok=True)
    outputs=[]
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        step=1 if mode=='pages' else chunk_size
        for start in range(0,len(doc),step):
            target=folder/f'{source.stem}_pages_{start+1:04d}-{min(start+step,len(doc)):04d}.pdf'
            if target.resolve()==source.resolve(): raise PDFOperationError('Écrasement source interdit.')
            with fitz.open() as part:
                part.insert_pdf(doc,from_page=start,to_page=min(start+step,len(doc))-1)
                part.save(target,garbage=4,deflate=True)
            outputs.append(target)
    return outputs

def compress_pdf(source,output):
    source=_inputs([source])[0]; output=_output(output,[source])
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        doc.save(output,garbage=4,deflate=True,deflate_images=True,deflate_fonts=True,clean=True)
    return [output]

def extract_text(source,output):
    source=_inputs([source])[0]; output=Path(output)
    if output.suffix.lower()!='.txt': raise PDFOperationError('La sortie doit être un TXT.')
    if output.resolve()==source.resolve(): raise PDFOperationError('Écrasement source interdit.')
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        content='\n\n'.join(page.get_text(sort=True) for page in doc)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(content,encoding='utf-8')
    return [output]

def pdf_to_docx(source,output):
    from docx import Document
    source=_inputs([source])[0]; output=Path(output)
    if output.suffix.lower()!='.docx': raise PDFOperationError('La sortie doit être un DOCX.')
    document=Document()
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        for index,page in enumerate(doc):
            if index: document.add_page_break()
            text=page.get_text(sort=True)
            for line in text.splitlines(): document.add_paragraph(line)
    output.parent.mkdir(parents=True,exist_ok=True)
    document.save(output)
    return [output]

# Excel cells are limited to 32,767 UTF-16 code units. Do not truncate PDF
# text silently, and never let an untrusted PDF line become an Excel formula.
_XLSX_CELL_LIMIT = 32767
_XLSX_ROW_LIMIT = 1048576


def _excel_text_fragments(value):
    """Yield exact consecutive UTF-16-bounded fragments (no lost characters).

    Split at a space when possible to preserve whole lexical tokens; retain
    the space in the following fragment so joining all parts reproduces the
    original input exactly. Astral Unicode characters count as two units.
    """
    if not value:
        yield ''
        return
    cursor = 0
    while cursor < len(value):
        units = 0
        end = cursor
        while end < len(value):
            char_units = 2 if ord(value[end]) > 0xFFFF else 1
            if units + char_units > _XLSX_CELL_LIMIT:
                break
            units += char_units
            end += 1
        if end < len(value):
            # Prefer a word boundary in the last quarter of this fragment.
            boundary = value.rfind(' ', cursor + (end - cursor) * 3 // 4, end)
            if boundary > cursor:
                end = boundary
        if end <= cursor:
            raise PDFOperationError('Fragment Excel invalide')
        yield value[cursor:end]
        cursor = end


def pdf_to_xlsx(source,output):
    from openpyxl import Workbook
    source=_inputs([source])[0]; output=Path(output)
    if output.suffix.lower()!='.xlsx': raise PDFOperationError('La sortie doit être un XLSX.')
    wb=Workbook(); ws=wb.active; ws.title='Texte PDF'
    ws.append(['Page','Ligne','Texte','Segment'])
    rows = 1
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        for page_num,page in enumerate(doc,1):
            for line_num,line in enumerate(page.get_text(sort=True).splitlines(),1):
                for segment,part in enumerate(_excel_text_fragments(line),1):
                    if rows >= _XLSX_ROW_LIMIT:
                        raise PDFOperationError('Nombre maximal de lignes Excel dépassé')
                    rows += 1
                    ws.append([page_num,line_num,part,segment])
                    # openpyxl normally interprets values starting with '=' as
                    # formulas. Force a literal cell WITHOUT adding an apostrophe
                    # that would change the extracted document text.
                    ws.cell(row=rows,column=3).data_type='s'
    output.parent.mkdir(parents=True,exist_ok=True); wb.save(output)
    return [output]

def pdf_to_pptx(source, output):
    """Export all extractable PDF text as editable, paginated PPTX slides.

    A PDF page may require multiple slides. Original PDF geometry and images
    are not reconstructed. Oversized inputs fail without silent truncation.
    """
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.text import MSO_AUTO_SIZE
    from openpdf_pptx_pagination_v458 import chunks_for_page

    source = _inputs([source])[0]
    output = Path(output)
    if output.suffix.lower() != '.pptx':
        raise PDFOperationError('La sortie doit être un PPTX.')
    prs = Presentation()
    with fitz.open(source) as doc:
        if doc.needs_pass:
            raise PDFOperationError('PDF protégé.')
        for page_number, page in enumerate(doc, 1):
            # Extractable text only: scanned pages require OCR beforehand.
            chunks = chunks_for_page(page.get_text(sort=True))
            for chunk_number, chunk in enumerate(chunks, 1):
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                heading = slide.shapes.add_textbox(Inches(.5), Inches(.3),
                                                   Inches(9), Inches(.5))
                heading.text = (f'Page {page_number} — partie {chunk_number}/{len(chunks)}'
                                if len(chunks) > 1 else f'Page {page_number}')
                body = slide.shapes.add_textbox(Inches(.5), Inches(1),
                                                Inches(9), Inches(6))
                body.text = chunk
                body.text_frame.word_wrap = True
                body.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
                for paragraph in body.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(14)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)
    return [output]
