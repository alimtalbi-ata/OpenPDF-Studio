"""Atomic page operations independent of Tkinter. Author: Abdelhalim Talbi."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import tempfile
import fitz
from openpdf_atomic_output import publish_exclusive
from openpdf_page_source_integrity_v435 import snapshot_source, verify_source as verify_source_snapshot

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
    """Reject a final-component symlink before resolving it to its target."""
    candidate = Path(path).expanduser()
    if candidate.is_symlink():
        raise ValueError('Source PDF via lien symbolique interdit')
    p = candidate.resolve(strict=True)
    # Recheck the lexical path to catch a link introduced during resolution.
    if candidate.is_symlink():
        raise ValueError('Source PDF via lien symbolique interdit')
    if not p.is_file() or p.suffix.lower() != '.pdf':
        raise ValueError('Source PDF invalide')
    return p

def _target(path,sources):
    p=Path(path).resolve()
    if p.suffix.lower()!='.pdf' or p in sources:raise ValueError('Destination PDF invalide ou source écrasée')
    if not p.parent.is_dir():raise ValueError('Dossier de destination inexistant')
    if p.exists():raise FileExistsError(f'Destination existante : {p}')
    return p

def _publish(destination,writer,expected_pages=None,pre_publish=None):
    fd,tmp=tempfile.mkstemp(prefix='.openpdf-pages-',suffix='.pdf',dir=destination.parent)
    os.close(fd)
    try:
        writer(tmp)
        with fitz.open(tmp) as check:
            if check.page_count<1 or check.needs_pass:raise ValueError('PDF produit invalide')
            pages=check.page_count
            if expected_pages is not None and pages != expected_pages:
                raise ValueError(f'Nombre de pages inattendu : {pages} au lieu de {expected_pages}')
        digest = _digest(tmp)
        if pre_publish is not None:pre_publish()
        publish_exclusive(tmp, destination)
        return str(destination),pages,digest
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def _source_identity(path):
    stat=Path(path).stat()
    return (stat.st_size,stat.st_mtime_ns,stat.st_ino)

def _source_fingerprint(path):
    """Detect concurrent edits while capturing a source's content digest."""
    before=_source_identity(path)
    try:
        checksum=_digest(path)
        after=_source_identity(path)
    except OSError as exc:
        raise RuntimeError('Source indisponible pendant la fusion : sortie rejetée') from exc
    if after!=before:
        raise RuntimeError('Source modifiée pendant la fusion : sortie rejetée')
    return before,checksum

def _verify_source_fingerprint(path,fingerprint):
    """Check both metadata and bytes; timestamps alone can be restored."""
    try:
        if _source_identity(path)!=fingerprint[0] or _digest(path)!=fingerprint[1]:
            raise RuntimeError('Source modifiée pendant la fusion : sortie rejetée')
    except OSError as exc:
        raise RuntimeError('Source indisponible pendant la fusion : sortie rejetée') from exc

def merge(sources,destination):
    paths=[_source(p) for p in sources]
    if not paths:raise ValueError('Aucune source')
    dest=_target(destination,set(paths))
    fingerprints={path:snapshot_source(path) for path in paths}
    from openpdf_merge_navigation_v478 import (prepare_merge_navigation,
        apply_merge_navigation, verify_merge_navigation)
    bookmarks, expected = prepare_merge_navigation(paths)
    from openpdf_link_fidelity_v480 import prepare_link_plan, apply_link_plan, verify_link_plan
    segments = []
    for path in paths:
        with fitz.open(path) as doc:
            segments.append((path, list(range(1, doc.page_count + 1))))
    link_plan = prepare_link_plan(segments)
    from openpdf_page_labels_v482 import prepare_label_plan, apply_label_plan, verify_label_plan
    label_plan = prepare_label_plan(segments)
    from openpdf_annotation_fidelity_v481 import prepare_annotation_plan, verify_annotation_plan
    annotation_plan = prepare_annotation_plan(segments)
    def writer(tmp):
        with fitz.open() as result:
            for path in paths:
                with fitz.open(path) as doc:
                    if doc.needs_pass or doc.page_count==0:raise ValueError('PDF source vide ou protégé')
                    result.insert_pdf(doc, links=False)
            apply_merge_navigation(result, bookmarks)
            apply_link_plan(result, link_plan)
            apply_label_plan(result, label_plan)
            result.save(tmp,garbage=3,deflate=True)
        with fitz.open(tmp) as check:
            verify_merge_navigation(check, bookmarks)
            verify_link_plan(check, link_plan)
            verify_label_plan(check, label_plan)
            verify_annotation_plan(check, annotation_plan)
        from openpdf_page_visual_fidelity_v483 import validate_page_visual_fidelity
        validate_page_visual_fidelity(segments, tmp)
        from openpdf_page_text_fidelity_v484 import validate_page_text_fidelity
        validate_page_text_fidelity(segments, tmp)
        from openpdf_glyph_fidelity_v485 import validate_page_glyph_fidelity
        validate_page_glyph_fidelity(segments, tmp)
    def verify_sources():
        for path,fingerprint in fingerprints.items():
            verify_source_snapshot(path,fingerprint)
    p,n,h=_publish(dest,writer,expected_pages=expected,pre_publish=verify_sources)
    return PageReceipt('merge',(p,),(n,),(h,))

def extract(source,destination,first,last):
    src=_source(source);dest=_target(destination,{src})
    fingerprint=snapshot_source(src)
    if not isinstance(first,int) or isinstance(first,bool) or not isinstance(last,int) or isinstance(last,bool) or first<1 or last<first:raise ValueError('Plage invalide')
    from openpdf_page_navigation_v479 import (prepare_page_navigation, apply_page_navigation,
                                               verify_page_navigation)
    bookmarks=prepare_page_navigation(src, list(range(first,last+1)))
    from openpdf_link_fidelity_v480 import prepare_link_plan, apply_link_plan, verify_link_plan
    segments = [(src, list(range(first,last+1)))]
    link_plan=prepare_link_plan(segments)
    from openpdf_page_labels_v482 import prepare_label_plan, apply_label_plan, verify_label_plan
    label_plan=prepare_label_plan([(src,list(range(first,last+1)))])
    from openpdf_annotation_fidelity_v481 import prepare_annotation_plan, verify_annotation_plan
    annotation_plan=prepare_annotation_plan([(src,list(range(first,last+1)))])
    from openpdf_metadata_fidelity_v501 import prepare_metadata, apply_metadata, verify_metadata
    with fitz.open(src) as metadata_source:
        metadata_plan = prepare_metadata(metadata_source)
    def writer(tmp):
        with fitz.open(src) as doc:
            if doc.needs_pass or last>doc.page_count:raise ValueError('Plage hors limites ou PDF protégé')
            with fitz.open() as out:
                out.insert_pdf(doc,from_page=first-1,to_page=last-1,links=False)
                apply_page_navigation(out,bookmarks)
                apply_link_plan(out,link_plan)
                apply_label_plan(out,label_plan)
                apply_metadata(out, metadata_plan)
                out.save(tmp,garbage=3,deflate=True)
        with fitz.open(tmp) as check:
            verify_metadata(check, metadata_plan)
            verify_page_navigation(check,bookmarks)
            verify_link_plan(check,link_plan)
            verify_label_plan(check,label_plan)
            verify_annotation_plan(check,annotation_plan)
        from openpdf_page_visual_fidelity_v483 import validate_page_visual_fidelity
        validate_page_visual_fidelity(segments, tmp)
        from openpdf_page_text_fidelity_v484 import validate_page_text_fidelity
        validate_page_text_fidelity(segments, tmp)
        from openpdf_glyph_fidelity_v485 import validate_page_glyph_fidelity
        validate_page_glyph_fidelity(segments, tmp)
    def verify_source():
        verify_source_snapshot(src,fingerprint)
    p,n,h=_publish(dest,writer,expected_pages=last-first+1,pre_publish=verify_source)
    return PageReceipt('extract',(p,),(n,),(h,))

def reorder(source,destination,indices):
    src=_source(source);dest=_target(destination,{src})
    fingerprint=snapshot_source(src)
    if not isinstance(indices,(list,tuple)) or not indices or any(not isinstance(i,int) or isinstance(i,bool) for i in indices):raise ValueError('Ordre invalide')
    from openpdf_page_navigation_v479 import (prepare_page_navigation, apply_page_navigation,
                                               verify_page_navigation)
    bookmarks=prepare_page_navigation(src,indices)
    from openpdf_link_fidelity_v480 import prepare_link_plan, apply_link_plan, verify_link_plan
    segments = [(src, indices)]
    link_plan=prepare_link_plan(segments)
    from openpdf_page_labels_v482 import prepare_label_plan, apply_label_plan, verify_label_plan
    label_plan=prepare_label_plan([(src,indices)])
    from openpdf_annotation_fidelity_v481 import prepare_annotation_plan, verify_annotation_plan
    annotation_plan=prepare_annotation_plan([(src,indices)])
    from openpdf_metadata_fidelity_v501 import prepare_metadata, apply_metadata, verify_metadata
    with fitz.open(src) as metadata_source:
        metadata_plan = prepare_metadata(metadata_source)
    def writer(tmp):
        with fitz.open(src) as doc:
            if doc.needs_pass or any(i<1 or i>doc.page_count for i in indices):raise ValueError('Page inexistante ou PDF protégé')
            with fitz.open() as out:
                for i in indices:out.insert_pdf(doc,from_page=i-1,to_page=i-1,links=False)
                apply_page_navigation(out,bookmarks)
                apply_link_plan(out,link_plan)
                apply_label_plan(out,label_plan)
                apply_metadata(out, metadata_plan)
                out.save(tmp,garbage=3,deflate=True)
        with fitz.open(tmp) as check:
            verify_metadata(check, metadata_plan)
            verify_page_navigation(check,bookmarks)
            verify_link_plan(check,link_plan)
            verify_label_plan(check,label_plan)
            verify_annotation_plan(check,annotation_plan)
        from openpdf_page_visual_fidelity_v483 import validate_page_visual_fidelity
        validate_page_visual_fidelity(segments, tmp)
        from openpdf_page_text_fidelity_v484 import validate_page_text_fidelity
        validate_page_text_fidelity(segments, tmp)
        from openpdf_glyph_fidelity_v485 import validate_page_glyph_fidelity
        validate_page_glyph_fidelity(segments, tmp)
    def verify_source():
        verify_source_snapshot(src,fingerprint)
    p,n,h=_publish(dest,writer,expected_pages=len(indices),pre_publish=verify_source)
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
        # Rollback is best effort: a matching digest reduces accidental removal,
        # but cannot prevent a concurrent replacement between hash and unlink.
        for receipt in published:
            output = Path(receipt.outputs[0])
            try:
                if output.is_file() and _digest(output) == receipt.sha256[0]:
                    output.unlink()
            except OSError:
                pass
        raise
    return PageReceipt('split',tuple(x.outputs[0] for x in published),tuple(x.page_counts[0] for x in published),tuple(x.sha256[0] for x in published))
