"""Reproducible synthetic corpus and structural indicators; not visual fidelity. Abdelhalim Talbi."""
from dataclasses import dataclass,asdict
from pathlib import Path
import fitz,json
from openpdf_fidelity_v352 import measure_text_coverage

@dataclass(frozen=True)
class StructuralMetrics:
    pages:int
    text_blocks:int
    embedded_images:int
    vector_drawings:int

def pdf_metrics(path):
    with fitz.open(path) as pdf:
        if pdf.needs_pass: raise ValueError('PDF protégé')
        return StructuralMetrics(len(pdf),sum(len(p.get_text('blocks')) for p in pdf),sum(len(p.get_images(full=True)) for p in pdf),sum(len(p.get_drawings()) for p in pdf))

def benchmark_case(source,output):
    source=Path(source); output=Path(output)
    if not source.is_file() or not output.is_file(): raise FileNotFoundError('Document source ou sortie absent')
    cov=measure_text_coverage(source,output)
    return {'source':source.name,'output':output.name,'source_structure':asdict(pdf_metrics(source)),'text_coverage':asdict(cov),'limits':['Aucune fidélité visuelle mesurée','Les objets Office ne sont pas comparés géométriquement']}

def build_synthetic_corpus(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    cases=[('01-texte-simple.pdf','Titre exemple\nAlpha beta gamma delta'),('02-multipage.pdf','Page alpha beta'),('03-tableau-dessine.pdf','Colonne A    Colonne B')]
    paths=[]
    for name,content in cases:
        p=directory/name
        with fitz.open() as doc:
            page=doc.new_page();page.insert_text((50,70),content)
            if 'multipage' in name:doc.new_page().insert_text((50,70),'Deuxieme page gamma')
            if 'tableau' in name:
                for x in (45,210,400):page.draw_line((x,90),(x,160))
                for y in (90,125,160):page.draw_line((45,y),(400,y))
            doc.save(p)
        paths.append(p)
    return paths

def write_report(cases,destination):
    destination=Path(destination);destination.write_text(json.dumps({'dataset':'SYNTHETIQUE - ne pas assimiler a une mesure terrain','cases':cases},ensure_ascii=False,indent=2),encoding='utf-8')
    return destination
