"""V26.1: PDF preview and page editing. Author: Abdelhalim Talbi."""
from pathlib import Path
import fitz
from openpdf_core_v260 import _inputs, _output, PDFOperationError

def page_info(source):
    source=_inputs([source])[0]
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        return [{'number':i+1,'width':round(p.rect.width),'height':round(p.rect.height),'rotation':p.rotation} for i,p in enumerate(doc)]

def preview_png(source,page=1,max_width=500,max_height=650):
    source=_inputs([source])[0]
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        if not isinstance(page,int) or not 1<=page<=len(doc): raise PDFOperationError('Numéro de page invalide.')
        if not 32<=max_width<=2048 or not 32<=max_height<=2048: raise PDFOperationError('Dimensions invalides.')
        p=doc[page-1]; scale=min(max_width/p.rect.width,max_height/p.rect.height,2)
        return p.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).tobytes('png')

def edit_pages(source,output,keep_pages=None,rotate_pages=None):
    source=_inputs([source])[0];output=_output(output,[source])
    with fitz.open(source) as doc:
        if doc.needs_pass: raise PDFOperationError('PDF protégé.')
        n=len(doc)
        keep=list(range(1,n+1)) if keep_pages is None else list(keep_pages)
        if not keep or len(set(keep))!=len(keep) or any(not isinstance(i,int) or isinstance(i,bool) or not 1<=i<=n for i in keep):
            raise PDFOperationError('Sélection de pages invalide (doublons ou hors limites).')
        rotations=rotate_pages or {}
        if any(not isinstance(k,int) or k not in keep or v not in (0,90,180,270) for k,v in rotations.items()):
            raise PDFOperationError('Rotations invalides.')
        with fitz.open() as result:
            for index in keep:
                result.insert_pdf(doc,from_page=index-1,to_page=index-1)
                if index in rotations: result[-1].set_rotation(rotations[index])
            result.save(output,garbage=4,deflate=True)
    return [output]
