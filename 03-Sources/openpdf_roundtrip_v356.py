"""V35.6 roundtrip: visual and structural evidence. Author: Abdelhalim Talbi."""
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,shutil,subprocess,tempfile,json
from openpdf_conversion_service_v351 import convert_office
from openpdf_visual_fidelity_v354 import compare_pdf_renders
from openpdf_quality_metrics_v356 import compare_structure

@dataclass(frozen=True)
class Qualification:
    source_sha256:str
    office_format:str
    office_sha256:str
    visual:dict
    structure:dict
    warnings:tuple

def qualify(source,*,office_format='docx',libreoffice=None,dpi=96,max_pages=30,timeout=120):
    if office_format not in ('docx','xlsx','pptx'):raise ValueError('Format inconnu')
    if not isinstance(timeout,int) or not 1<=timeout<=3600:raise ValueError('Timeout invalide')
    source=Path(source).resolve()
    if not source.is_file() or source.suffix.lower()!='.pdf':raise ValueError('PDF source invalide')
    executable=libreoffice or shutil.which('libreoffice') or shutil.which('soffice')
    if not executable:raise RuntimeError('LibreOffice indisponible')
    with tempfile.TemporaryDirectory(prefix='openpdf-v356-') as directory:
        folder=Path(directory); office=folder/('document.'+office_format)
        result=convert_office(source,office,output_format=office_format)
        rendered=folder/'rendered';rendered.mkdir()
        command=[str(executable),'--headless','-env:UserInstallation='+ (folder/'lo-profile').as_uri(),'--convert-to','pdf','--outdir',str(rendered),str(office)]
        try:process=subprocess.run(command,capture_output=True,text=True,timeout=timeout,check=False)
        except subprocess.TimeoutExpired as error:raise RuntimeError('Export PDF expiré') from error
        pdf=rendered/'document.pdf'
        if process.returncode or not pdf.is_file() or not pdf.stat().st_size:raise RuntimeError('Export Office vers PDF impossible: '+(process.stderr or process.stdout)[-300:])
        visual=compare_pdf_renders(source,pdf,dpi=dpi,max_pages=max_pages)
        structure=compare_structure(source,pdf,max_pages=max_pages)
        warnings=tuple(visual.warnings)+tuple(structure.warnings)+tuple(result.warnings)
        return Qualification(hashlib.sha256(source.read_bytes()).hexdigest(),office_format,result.sha256,asdict(visual),asdict(structure),warnings)

def save_qualification(report,path):
    path=Path(path);path.write_text(json.dumps(asdict(report),ensure_ascii=False,indent=2),encoding='utf8');return path
