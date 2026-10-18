"""Atomic page operations independent of Tkinter. Author: Abdelhalim Talbi."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import tempfile
import fitz
from openpdf_atomic_output import publish_exclusive

@dataclass(frozen=True)
class PageReceipt:
    operation: str
    outputs: tuple[str, ...]
    page_counts: tuple[int, ...]
    sha256: tuple[str, ...]

def _digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def _source(path):
    p=Path(path).resolve(strict=True)
    if not p.is_file() or p.suffix.lower()!='.pdf':raise ValueError('Source PDF invalide')
    return p

def _target(path,sources):
    p=Path(path).resolve()
    if p.suffix.lower()!='.pdf' or p in sources:raise ValueError('Destination PDF invalide ou source écrasée')
    if not p.parent.is_dir():raise ValueError('Dossier de destination inexistant')
    if p.exists():raise FileExistsError(f'Destination existante : {p}')
    return p

def _publish(destination,writer):
    fd,tmp=tempfile.mkstemp(prefix='.openpdf-pages-',suffix='.pdf',dir=destination.parent)
    os.close(fd)
    try:
        writer(tmp)
        with fitz.open(tmp) as check:
            if check.page_count<1 or check.needs_pass:raise ValueError('PDF produit invalide')
            pages=check.page_count
        digest = _digest(tmp)
        publish_exclusive(tmp, destination)
        return str(destination),pages,digest
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def merge(sources,destination):
    paths=[_source(p) for p in sources]
    if not paths:raise ValueError('Aucune source')
    dest=_target(destination,set(paths))
    def writer(tmp):
        with fitz.open() as result:
            for path in paths:
                with fitz.open(path) as doc:
                    if doc.needs_pass or doc.page_count==0:raise ValueError('PDF source vide ou protégé')
                    result.insert_pdf(doc)
            result.save(tmp,garbage=3,deflate=True)
    p,n,h=_publish(dest,writer)
    return PageReceipt('merge',(p,),(n,),(h,))

def extract(source,destination,first,last):
    src=_source(source);dest=_target(destination,{src})
    if not isinstance(first,int) or isinstance(first,bool) or not isinstance(last,int) or isinstance(last,bool) or first<1 or last<first:raise ValueError('Plage invalide')
    def writer(tmp):
        with fitz.open(src) as doc:
            if doc.needs_pass or last>doc.page_count:raise ValueError('Plage hors limites ou PDF protégé')
            with fitz.open() as out:
                out.insert_pdf(doc,from_page=first-1,to_page=last-1)
                out.save(tmp,garbage=3,deflate=True)
    p,n,h=_publish(dest,writer)
    return PageReceipt('extract',(p,),(n,),(h,))

def reorder(source,destination,indices):
    src=_source(source);dest=_target(destination,{src})
    if not isinstance(indices,(list,tuple)) or not indices or any(not isinstance(i,int) or isinstance(i,bool) for i in indices):raise ValueError('Ordre invalide')
    def writer(tmp):
        with fitz.open(src) as doc:
            if doc.needs_pass or any(i<1 or i>doc.page_count for i in indices):raise ValueError('Page inexistante ou PDF protégé')
            with fitz.open() as out:
                for i in indices:out.insert_pdf(doc,from_page=i-1,to_page=i-1)
                out.save(tmp,garbage=3,deflate=True)
    p,n,h=_publish(dest,writer)
    return PageReceipt('reorder',(p,),(n,),(h,))

def split(source,folder,chunk_size=1):
    src=_source(source);dest=Path(folder).resolve()
    if not dest.is_dir():raise ValueError('Dossier de destination inexistant')
    if not isinstance(chunk_size,int) or isinstance(chunk_size,bool) or chunk_size<1:raise ValueError('Taille de lot invalide')
    with fitz.open(src) as doc:
        if doc.needs_pass or not doc.page_count:raise ValueError('PDF source vide ou protégé')
        n=doc.page_count
    # Fail closed: no overwrite of existing outputs; avoids partial replacement of prior runs.
    targets=[dest/f'{src.stem}_pages_{i+1:04d}-{min(i+chunk_size,n):04d}.pdf' for i in range(0,n,chunk_size)]
    if any(p.exists() or p.resolve()==src for p in targets):raise FileExistsError('Sortie déjà existante : découpage interrompu')
    published=[]
    try:
        for i,target in zip(range(0,n,chunk_size),targets):
            receipt=extract(src,target,i+1,min(i+chunk_size,n))
            published.append(receipt)
    except BaseException:
        # Do not delete a path merely by name: another process may have
        # replaced it after our publication. Roll back only matching bytes.
        for receipt in published:
            output = Path(receipt.outputs[0])
            try:
                if output.is_file() and _digest(output) == receipt.sha256[0]:
                    output.unlink()
            except OSError:
                pass
        raise
    return PageReceipt('split',tuple(x.outputs[0] for x in published),tuple(x.page_counts[0] for x in published),tuple(x.sha256[0] for x in published))
