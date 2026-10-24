"""Validate per-page decoded image pixels and placement for lossless PDF compression.
Author: Abdelhalim Talbi.
"""
from collections import Counter
import hashlib
import fitz

def _fingerprints(document):
    pages=[]
    for page in document:
        images=Counter()
        for item in page.get_images(full=True):
            xref=item[0]
            pix=fitz.Pixmap(document,xref)
            identity=(pix.width,pix.height,pix.n,pix.alpha,hashlib.sha256(pix.samples).hexdigest())
            # get_image_rects returns the actual occurrences and their geometry,
            # including repeated placements of a single image resource.
            placements=page.get_image_rects(xref,transform=True)
            for rectangle,matrix in placements:
                geometry=tuple(round(float(v),5) for v in (*rectangle,*matrix))
                images[(identity,geometry)]+=1
        pages.append(images)
    return pages

def validate_lossless_images(source,candidate):
    with fitz.open(source) as before,fitz.open(candidate) as after:
        if before.needs_pass or after.needs_pass: raise ValueError('PDF protégé')
        if before.page_count != after.page_count: raise ValueError('Nombre de pages modifié')
        original=_fingerprints(before)
        optimized=_fingerprints(after)
    for index,(a,b) in enumerate(zip(original,optimized),1):
        if a != b:
            raise RuntimeError(f'Images ou positions modifiées à la page {index} dans un profil sans perte : sortie rejetée')
    return {'images_verified':sum(sum(page.values()) for page in original),'pages_verified':len(original)}
