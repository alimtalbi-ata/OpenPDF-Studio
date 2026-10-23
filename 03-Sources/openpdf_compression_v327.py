"""V32.7 : compression image optionnelle, avertissement de perte. Abdelhalim Talbi."""
from pathlib import Path
import os,tempfile
from openpdf_compression_v319 import validate_compression
from openpdf_engine_v272 import compress_pdf
from openpdf_compression_v320 import format_bytes
from openpdf_atomic_output import publish_exclusive

def diagnose_pdf(source):
    """Mesures factuelles du PDF ; aucune promesse de réduction."""
    import fitz
    path=Path(source)
    with fitz.open(str(path)) as doc:
        pages=len(doc)
        images=sum(len(page.get_images(full=True)) for page in doc)
        text_pages=sum(bool(page.get_text('text').strip()) for page in doc)
    category=('Principalement numérisé / images' if images and text_pages < max(1,pages//2)
              else 'Mixte texte et images' if images else 'Principalement texte / vectoriel')
    return {'pages':pages,'images':images,'pages_avec_texte':text_pages,'categorie':category,'octets':path.stat().st_size}

PROFILES = {"standard": "Optimisation sans perte", "smaller_only": "Conserver uniquement si plus petit", "images_balanced": "Images — compression avec perte (150 dpi, JPEG 75)", "images_adaptive": "Images — adaptatif (JPEG 55/70/85, qualité contrôlée)"}

def compress_images(source, destination, *, dpi_target=150, quality=75):
    """Réencode certaines images embarquées ; conserve pages et texte vectoriel.

    Ne rasterise jamais les pages. Refuse les PyMuPDF trop anciens plutôt que de
    prétendre avoir effectué une compression d'images.
    """
    import fitz
    if not (72 <= dpi_target <= 300 and 30 <= quality <= 95):
        raise ValueError('Paramètres image hors limites')
    with fitz.open(str(source)) as doc:
        if doc.needs_pass: raise ValueError('PDF protégé : mot de passe requis')
        if not hasattr(doc,'rewrite_images'):
            raise RuntimeError('PyMuPDF incompatible : rewrite_images indisponible')
        count=len(doc)
        doc.rewrite_images(dpi_threshold=dpi_target+20,dpi_target=dpi_target,quality=quality,
                           lossy=True,lossless=True,bitonal=False,color=True,gray=True)
        doc.save(str(destination),garbage=4,deflate=True,deflate_images=True,deflate_fonts=True)
    with fitz.open(str(destination)) as check:
        if len(check)!=count: raise RuntimeError('Contrôle de pages échoué')


def compress_with_profile(source, destination, profile="smaller_only", *, audit_collector=None):
    if profile not in PROFILES: raise ValueError("Profil inconnu")
    source,destination=validate_compression(source,destination)
    if Path(destination).exists() or Path(destination).is_symlink():
        raise FileExistsError(f'Destination existante : {destination}')
    from openpdf_source_integrity_v430 import fingerprint_source,verify_source_unchanged
    source_fingerprint=fingerprint_source(source)
    # V47.6: reject oversized image/page resources before allocating output.
    from openpdf_compression_preflight_v476 import preflight_compression_source
    preflight_compression_source(source)
    # Refuse protected/active documents before the compressor rewrites them.
    import fitz
    from openpdf_active_content_guard_v440 import reject_unsafe_rewrite
    with fitz.open(str(source)) as preflight:
        reject_unsafe_rewrite(preflight)
        from openpdf_accessibility_guard_v456 import reject_unverifiable_accessibility
        reject_unverifiable_accessibility(preflight)
    before=source_fingerprint.size
    fd,tmp=tempfile.mkstemp(prefix=".openpdf-",suffix=".pdf",dir=str(Path(destination).parent))
    os.close(fd)
    try:
        adaptive_report = None
        if profile == 'images_adaptive':
            from openpdf_adaptive_compression_v443 import select_adaptive_candidate
            selected, selected_bytes, adaptive_report = select_adaptive_candidate(
                source, tmp, compressor=compress_images,
                source_fingerprint=source_fingerprint)
            if selected is None:
                verify_source_unchanged(source, source_fingerprint)
                return ('Aucun gain : les candidats JPEG conformes sont aussi grands '
                        'que la source. Aucun fichier de sortie modifié.')
        else:
            (compress_images(source,tmp) if profile=="images_balanced" else compress_pdf(source,tmp))
        after=Path(tmp).stat().st_size
        # A candidate that cannot be published must not trigger expensive
        # full-document text, image and raster quality checks.
        if profile=='smaller_only' and after>=before:
            # Even rejected candidates must not conceal a concurrently changed source.
            verify_source_unchanged(source, source_fingerprint)
            return f"Aucun gain : original {format_bytes(before)}, candidat {format_bytes(after)}. Aucun fichier de sortie modifié."
        # Fail before opening the source for quality assessment if the input
        # disappeared or changed during the compressor's work.
        verify_source_unchanged(source, source_fingerprint)
        from openpdf_quality_v327 import assess_candidate,quality_summary
        assessment=assess_candidate(source,tmp)
        if assessment['pages_texte_modifie']:
            raise RuntimeError('Le texte extrait diffère sur certaines pages : sortie rejetée')
        # V47.4: extracted text may remain identical while its position changes.
        # Validate word coordinates before expensive raster checks and publication.
        from openpdf_text_geometry_v474 import validate_text_geometry
        validate_text_geometry(source, tmp)
        visual_report = None
        if profile in ('standard','smaller_only'):
            from openpdf_compression_quality_v422 import validate_lossless_images
            validate_lossless_images(source,tmp)
            from openpdf_render_quality_v425 import validate_rendered_pages
            validate_rendered_pages(source,tmp)
        else:
            from openpdf_lossy_quality_v436 import validate_lossy_render
            visual_report = validate_lossy_render(source, tmp)
        # Raster and extracted text checks cannot detect lost links, forms or annotations.
        from openpdf_structure_guard_v439 import validate_structure_preserved
        validate_structure_preserved(source, tmp)
        # Hash and file identity checks also cover deleted or replaced sources.
        verify_source_unchanged(source,source_fingerprint)
        # Optional quantitative audit runs on the private candidate BEFORE
        # publication. Any failure leaves the destination untouched.
        if audit_collector is not None:
            if not callable(audit_collector):
                raise TypeError('Audit de compression invalide')
            audit_collector(source, tmp)
            verify_source_unchanged(source, source_fingerprint)
        # Never overwrite a destination created while compression was running.
        publish_exclusive(tmp,destination)
        change=(before-after)*100/before if before else 0
        detail = (f"\nMAE visuelle max : {visual_report['max_mae']:.2f}/255 ; "
                  f"pixels altérés max : {visual_report['max_changed_fraction']:.1%} ; "
                  f"MAE locale max : {visual_report['max_tile_mae']:.2f}/255 ; "
                  f"pixels altérés locaux max : {visual_report['max_tile_changed_fraction']:.1%} ; "
                  f"{visual_report['pages_verified']} page(s) contrôlée(s). "
                  "Mesure par échantillonnage, non certification de fidélité.") if visual_report else ""
        adaptive_detail = ""
        if adaptive_report is not None:
            trials = "; ".join(
                f"Q{a['quality']} " +
                (f"conforme ({a['bytes']} octets, MAE {a['max_mae']:.2f}/255)"
                 if a['status'] == 'accepted' else
                 (f"sans gain ({a['bytes']} octets)" if a['status'] == 'no_gain'
                  else "rejeté par les contrôles"))
                for a in adaptive_report)
            adaptive_detail = (
                f"\nAdaptatif : JPEG qualité {selected} retenue après "
                f"{len(adaptive_report)} essais. Essais : {trials}."
            )
        return f"{destination}\n{quality_summary(assessment)}{detail}{adaptive_detail}"
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def choose_profile_dialog(app):
    """Choix explicite avec explications ; fermeture = annulation."""
    import tkinter as tk
    from tkinter import ttk
    dialog=tk.Toplevel(app)
    dialog.title('Profil de compression PDF')
    dialog.transient(app)
    dialog.resizable(False,False)
    result={'value':None}
    selected=tk.StringVar(value='smaller_only')
    frame=ttk.Frame(dialog,padding=18)
    frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Quel résultat souhaitez-vous conserver ?',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,12))
    ttk.Radiobutton(frame,text='Recommandé — conserver uniquement si plus petit',variable=selected,value='smaller_only').pack(anchor='w')
    ttk.Label(frame,text='Ne crée pas de sortie lorsque la réduction est nulle.',wraplength=440).pack(anchor='w',padx=24,pady=(0,12))
    ttk.Radiobutton(frame,text='Standard — enregistrer le PDF optimisé',variable=selected,value='standard').pack(anchor='w')
    ttk.Label(frame,text='Peut produire un fichier de taille identique ou supérieure.',wraplength=440).pack(anchor='w',padx=24,pady=(0,12))
    ttk.Radiobutton(frame,text='Images — équilibré (avec perte)',variable=selected,value='images_balanced').pack(anchor='w')
    ttk.Label(frame,text='Réencode certaines images (150 dpi, qualité JPEG 75). Peut altérer les détails. Gardez votre original.',wraplength=440).pack(anchor='w',padx=24,pady=(0,12))
    ttk.Radiobutton(frame,text='Images — adaptatif : comparer trois qualités JPEG et retenir la plus petite sortie validée',variable=selected,value='images_adaptive').pack(anchor='w')
    ttk.Label(frame,text='Trois essais au maximum ; plus lent mais refuse les dégradations détectées et les sorties plus volumineuses.',wraplength=440).pack(anchor='w',padx=24,pady=(0,12))
    ttk.Label(frame,text='Les deux premiers profils sont sans perte ; les profils Images peuvent dégrader les images. Le texte vectoriel reste éditable.' ,wraplength=440).pack(anchor='w',pady=(12,12))
    buttons=ttk.Frame(frame);buttons.pack(fill='x')
    def finish(value):
        result['value']=value
        dialog.destroy()
    ttk.Button(buttons,text='Annuler',command=lambda:finish(None)).pack(side='right',padx=(8,0))
    ttk.Button(buttons,text='Continuer',command=lambda:finish(selected.get())).pack(side='right')
    dialog.protocol('WM_DELETE_WINDOW',lambda:finish(None))
    dialog.grab_set();dialog.wait_window()
    return result['value']

def guided_compress(app, *, ask_source=None, ask_destination=None, choose_profile=None, confirm_replace=None, warn=None):
    if getattr(app,'busy',False) or getattr(app,'_v272_busy',False):return False
    from tkinter import filedialog,messagebox
    ask_source=ask_source or (lambda:filedialog.askopenfilename(parent=app,title='1/3 — PDF à optimiser',filetypes=[('PDF','*.pdf')]))
    ask_destination=ask_destination or (lambda name:filedialog.asksaveasfilename(parent=app,title='2/3 — PDF de sortie',initialfile=name,defaultextension='.pdf',filetypes=[('PDF','*.pdf')]))
    choose_profile=choose_profile or (lambda:choose_profile_dialog(app))
    warn=warn or (lambda msg:messagebox.showwarning('Optimiser un PDF',msg,parent=app))
    confirm_replace=confirm_replace or (lambda path:messagebox.askyesno('Remplacer ?',f'Le fichier existe :\n{path}\nLe remplacer si le profil produit un résultat ?',parent=app))
    source=ask_source()
    if not source:return False
    destination=ask_destination(Path(source).stem+'-optimise.pdf')
    if not destination:return False
    try:source,destination=validate_compression(source,destination)
    except ValueError as exc:warn(str(exc));return False
    try:
        diagnostic=diagnose_pdf(source)
    except Exception as exc:
        warn('PDF non analysable : '+str(exc));return False
    if not getattr(app,'_openpdf_skip_diagnostic_dialog',False):
        messagebox.showinfo('Diagnostic du PDF',
            f"{diagnostic['pages']} pages · {diagnostic['images']} images · {diagnostic['pages_avec_texte']} pages avec texte\n"
            f"Type : {diagnostic['categorie']}\n"
            'Profils sans perte disponibles ; le profil Images est avec perte et peut réduire la netteté.',parent=app)
    profile=choose_profile()
    if profile is None:return False
    if profile not in PROFILES:warn('Profil inconnu');return False
    if profile in ('images_balanced', 'images_adaptive') and not messagebox.askyesno('Attention : compression avec perte',
        'Certaines images seront réencodées et peuvent perdre en netteté. Conserver l’original et poursuivre ?',parent=app):return False
    if profile in ('images_balanced', 'images_adaptive'):
        from openpdf_preview_v326 import preview_dialog
        if not preview_dialog(app,source):return False
    # The publication primitive is intentionally exclusive. Never offer a
    # replacement that the engine cannot perform (and must not perform).
    for attempt in range(3):
        if not Path(destination).exists() and not Path(destination).is_symlink():
            break
        warn('Le fichier de destination existe déjà. Choisissez un autre nom : '
             'OpenPDF Studio protège les fichiers existants et ne les écrase pas.')
        if attempt == 2:
            return False
        destination = ask_destination(Path(source).stem + '-optimise-nouveau.pdf')
        if not destination:
            return False
        try:
            source, destination = validate_compression(source, destination)
        except ValueError as exc:
            warn(str(exc))
            return False
    app._run_pdf(compress_with_profile,source,destination,profile)
    return True

def connect(app):
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app,tk.Tk):return app
    panel=getattr(app,'_v311_essentials',None)
    if panel:
        for cell in panel.winfo_children():
            for widget in cell.winfo_children():
                if isinstance(widget,ttk.Button) and widget.cget('text') in ('Compresser','Optimiser'):
                    widget.configure(command=lambda:guided_compress(app))
    app.bind('<Control-Shift-c>',lambda event:guided_compress(app))
    return app
