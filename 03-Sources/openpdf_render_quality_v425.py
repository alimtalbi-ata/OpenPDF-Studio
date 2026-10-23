"""Conservative low-resolution render parity gate for lossless compression.
Author: Abdelhalim Talbi.
"""
import hashlib
import fitz

def _page_digest(page, scale, max_pixels):
    matrix=fitz.Matrix(scale,scale)
    bounds=page.rect
    width=int(bounds.width*scale+1)
    height=int(bounds.height*scale+1)
    if width <= 0 or height <= 0 or width*height > max_pixels:
        raise ValueError('Page trop grande ou invalide pour le contrôle de rendu')
    pix=page.get_pixmap(matrix=matrix,colorspace=fitz.csRGB,alpha=False,annots=True)
    if pix.width*pix.height > max_pixels:
        raise ValueError('Rendu trop volumineux pour le contrôle qualité')
    return (pix.width,pix.height,pix.n,hashlib.sha256(pix.samples).digest())

def validate_rendered_pages(source,candidate,*,scale=0.5,max_pixels=12000000):
    """Compare each rendered page; never silently skip a page."""
    if not (0.25 <= scale <= 2) or max_pixels < 10000:
        raise ValueError('Paramètres de contrôle de rendu invalides')
    with fitz.open(source) as original,fitz.open(candidate) as optimized:
        if original.needs_pass or optimized.needs_pass:
            raise ValueError('PDF protégé')
        if original.page_count != optimized.page_count:
            raise ValueError('Nombre de pages modifié')
        for index in range(original.page_count):
            source_page=original[index]
            candidate_page=optimized[index]
            # A low-resolution bitmap alone cannot certify the PDF page boxes.
            boxes=lambda p: (tuple(round(float(v),4) for v in p.mediabox),
                             tuple(round(float(v),4) for v in p.cropbox),int(p.rotation))
            if boxes(source_page) != boxes(candidate_page):
                raise RuntimeError(f'Géométrie PDF modifiée à la page {index+1} : sortie rejetée')
            a=_page_digest(source_page,scale,max_pixels)
            b=_page_digest(candidate_page,scale,max_pixels)
            if a != b:
                raise RuntimeError(f'Rendu visuel modifié à la page {index+1} : sortie rejetée')
        return {'pages_rendered':original.page_count,'scale':scale}
