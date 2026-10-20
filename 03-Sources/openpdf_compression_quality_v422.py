"""Validate decoded embedded images in lossless PDF compression. Abdelhalim Talbi."""
from collections import Counter
import hashlib
import fitz

def _fingerprints(document):
    result=Counter()
    for page in document:
        for item in page.get_images(full=True):
            pix=fitz.Pixmap(document,item[0])
            result[(pix.width,pix.height,pix.n,pix.alpha,hashlib.sha256(pix.samples).hexdigest())]+=1
    return result

def validate_lossless_images(source,candidate):
    with fitz.open(source) as before,fitz.open(candidate) as after:
        if before.needs_pass or after.needs_pass: raise ValueError('PDF protégé')
        if before.page_count != after.page_count: raise ValueError('Nombre de pages modifié')
        original=_fingerprints(before)
        optimized=_fingerprints(after)
    if original != optimized:
        raise RuntimeError('Images modifiées dans un profil sans perte : sortie rejetée')
    return {'images_verified':sum(original.values())}
