"""Thread-safe preview renderer. No Tk calls outside the main thread."""
from pathlib import Path

def render_preview(source, page=0, max_width=460, max_height=520):
    import fitz
    from PIL import Image
    source=str(Path(source).resolve())
    if max_width<1 or max_height<1:raise ValueError('Dimensions invalides')
    with fitz.open(source) as doc:
        if doc.needs_pass or not doc.page_count:raise ValueError('PDF protégé ou vide')
        page=max(0,min(int(page),doc.page_count-1))
        rect=doc[page].rect
        scale=min(max_width/rect.width,max_height/rect.height,1.5)
        pix=doc[page].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
        image=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        return {'source':source,'page':page,'pages':doc.page_count,'size':image.size,'pixels':image.tobytes()}
