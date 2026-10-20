"""Validate decoded images per page in lossless PDF compression.
Author: Abdelhalim Talbi.
"""
from collections import Counter
import hashlib
import fitz

def _fingerprints(document):
    """Keep page boundaries: moving images to another page is not lossless."""
    pages=[]
    for page in document:
        images=Counter()
        for item in page.get_images(full=True):
            pix=fitz.Pixmap(document,item[0])
            images[(pix.width,pix.height,pix.n,pix.alpha,hashlib.sha256(pix.samples).hexdigest())]+=1
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
            raise RuntimeError(f'Images modifiées à la page {index} dans un profil sans perte : sortie rejetée')
    return {'images_verified':sum(sum(page.values()) for page in original),'pages_verified':len(original)}
