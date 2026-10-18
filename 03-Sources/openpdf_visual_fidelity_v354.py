"""Deterministic page-render comparison. Requires PyMuPDF and Pillow. Author: Abdelhalim Talbi."""
from pathlib import Path
from dataclasses import dataclass, asdict
import fitz
from PIL import Image, ImageChops, ImageStat
import json

@dataclass(frozen=True)
class VisualReport:
    reference_pages: int
    candidate_pages: int
    compared_pages: int
    mean_absolute_error: float
    page_errors: tuple
    warnings: tuple

def compare_pdf_renders(reference, candidate, *, dpi=96, max_pages=30):
    if not 36 <= dpi <= 300 or not 1 <= max_pages <= 500:
        raise ValueError('Paramètres de rendu hors limites')
    reference, candidate = Path(reference), Path(candidate)
    if not reference.is_file() or not candidate.is_file():
        raise FileNotFoundError('Document de comparaison absent')
    with fitz.open(reference) as src, fitz.open(candidate) as dst:
        if src.needs_pass or dst.needs_pass: raise ValueError('Document chiffré non accessible')
        if not src.page_count or not dst.page_count: raise ValueError('PDF vide')
        count=min(src.page_count,dst.page_count,max_pages)
        errors=[]
        for i in range(count):
            a=src[i].get_pixmap(dpi=dpi,alpha=False,colorspace=fitz.csRGB)
            b=dst[i].get_pixmap(dpi=dpi,alpha=False,colorspace=fitz.csRGB)
            image_a=Image.frombytes('RGB',(a.width,a.height),a.samples)
            image_b=Image.frombytes('RGB',(b.width,b.height),b.samples)
            if image_a.size != image_b.size:
                image_b=image_b.resize(image_a.size,Image.Resampling.BICUBIC)
            delta=ImageChops.difference(image_a,image_b)
            errors.append(round(sum(ImageStat.Stat(delta).mean)/(3*255),6))
        warnings=[]
        if src.page_count != dst.page_count: warnings.append('Nombre de pages différent')
        if count < max(src.page_count,dst.page_count): warnings.append('Comparaison partielle: limite max_pages')
        return VisualReport(src.page_count,dst.page_count,count,round(sum(errors)/count,6),tuple(errors),tuple(warnings))

def write_visual_report(report, destination):
    Path(destination).write_text(json.dumps(asdict(report),indent=2,ensure_ascii=False),encoding='utf-8')
    return Path(destination)
