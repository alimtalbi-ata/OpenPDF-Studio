"""Pure workspace pagination and validation helpers. Author: Abdelhalim Talbi."""
from pathlib import Path

def page_window(current, total):
    if total < 1: raise ValueError('PDF sans page')
    return min(max(int(current), 0), total - 1)

def next_page(current, total):
    return page_window(current + 1, total)

def previous_page(current, total):
    return page_window(current - 1, total)

def validate_request(operation, sources, destination):
    from openpdf_ui_controller_v348 import OPERATIONS
    if operation not in OPERATIONS: raise ValueError('Opération inconnue')
    if not sources: raise ValueError('Ajoutez au moins un PDF')
    if operation != 'fusion' and len(sources) != 1: raise ValueError('Un seul PDF source requis')
    if not str(destination).strip(): raise ValueError('Destination obligatoire')
    resolved = [Path(p).expanduser().resolve() for p in sources]
    if len(set(resolved)) != len(resolved): raise ValueError('PDF source en doublon')
    for path in resolved:
        if not path.is_file() or path.stat().st_size == 0: raise ValueError(f'PDF source absent ou vide : {path}')
    if Path(destination).expanduser().is_symlink():
        raise FileExistsError('Destination lien symbolique interdite')
    dest = Path(destination).expanduser().resolve()
    if operation != 'decoupage' and dest.exists(): raise FileExistsError(f'Destination existante : {dest}')
    if operation not in ('docx','xlsx','pptx','decoupage') and dest.suffix.lower() != '.pdf':
        raise ValueError('La destination doit être un fichier PDF (.pdf)')
    if operation in ('docx','xlsx','pptx') and dest.suffix.lower() != '.' + operation:
        raise ValueError('Extension de destination incorrecte pour la conversion Office')
    if operation != 'decoupage' and dest in resolved: raise ValueError('Destination identique à une source')
    if operation == 'decoupage':
        if not dest.is_dir(): raise ValueError('Dossier de découpage absent')
    elif not dest.parent.is_dir(): raise ValueError('Dossier de destination absent')
    return tuple(str(p) for p in resolved), str(dest)
