"""Office roundtrip qualification; no silent fallback. Author: Abdelhalim Talbi."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, json, shutil, subprocess, tempfile
from openpdf_conversion_service_v351 import convert_office
from openpdf_visual_fidelity_v354 import compare_pdf_renders

@dataclass(frozen=True)
class RoundtripReport:
    source_sha256: str
    office_format: str
    office_sha256: str
    visual: dict
    warnings: tuple

def qualify_roundtrip(source, *, office_format='docx', libreoffice=None, dpi=96, max_pages=30, timeout=120):
    if office_format not in ('docx','xlsx','pptx'): raise ValueError('Format non pris en charge')
    if not 1 <= timeout <= 3600: raise ValueError('Timeout invalide')
    source=Path(source).resolve()
    if not source.is_file() or source.suffix.lower()!='.pdf': raise ValueError('Source PDF invalide')
    executable=libreoffice or shutil.which('libreoffice') or shutil.which('soffice')
    if not executable: raise RuntimeError('LibreOffice absent : qualification non exécutée')
    with tempfile.TemporaryDirectory(prefix='openpdf-roundtrip-') as directory:
        tmp=Path(directory); office=tmp/('document.'+office_format)
        outcome=convert_office(source,office,output_format=office_format)
        rendered=tmp/'rendered'; rendered.mkdir()
        cmd=[str(executable),'--headless','--convert-to','pdf','--outdir',str(rendered),str(office)]
        try:
            proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError('Conversion Office vers PDF expirée') from exc
        candidate=rendered/'document.pdf'
        if proc.returncode or not candidate.is_file() or not candidate.stat().st_size:
            raise RuntimeError('Export PDF Office impossible : '+(proc.stderr or proc.stdout)[-400:])
        visual=compare_pdf_renders(source,candidate,dpi=dpi,max_pages=max_pages)
        warnings=list(visual.warnings)+list(outcome.warnings)
        return RoundtripReport(hashlib.sha256(source.read_bytes()).hexdigest(),office_format,outcome.sha256,asdict(visual),tuple(warnings))

def save_report(report,destination):
    Path(destination).write_text(json.dumps(asdict(report),ensure_ascii=False,indent=2),encoding='utf-8')
