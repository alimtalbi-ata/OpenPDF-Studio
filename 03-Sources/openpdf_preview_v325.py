"""V32.5 : comparaison visuelle d'une page, sans altérer la source. Abdelhalim Talbi."""
from pathlib import Path
import tempfile

def render_comparison(source, page_index=0, *, dpi=100, quality=75):
    """Return two PNG byte strings (original, compressed candidate), page sample only.

    The source is never changed. A full document must still be checked separately.
    """
    import fitz
    from openpdf_compression_v324 import compress_images
    if not 72 <= dpi <= 180: raise ValueError('DPI aperçu hors limites')
    with fitz.open(str(source)) as doc:
        if doc.needs_pass: raise ValueError('PDF protégé')
        if not 0 <= page_index < len(doc): raise IndexError('Page hors limites')
        original=doc[page_index].get_pixmap(dpi=dpi,alpha=False).tobytes('png')
        with tempfile.TemporaryDirectory(prefix='openpdf-preview-') as tmp:
            sample=Path(tmp)/'sample.pdf';candidate=Path(tmp)/'candidate.pdf'
            with fitz.open() as one:
                one.insert_pdf(doc,from_page=page_index,to_page=page_index)
                one.save(str(sample))
            compress_images(sample,candidate,quality=quality)
            with fitz.open(str(candidate)) as after:
                modified=after[0].get_pixmap(dpi=dpi,alpha=False).tobytes('png')
    return original,modified

def preview_dialog(app,source, *, page_index=0):
    """Explicit acceptance after showing real before/after renderings."""
    import tkinter as tk
    from tkinter import ttk,messagebox
    from io import BytesIO
    try:
        from PIL import Image,ImageTk
        before,after=render_comparison(source,page_index)
    except Exception as exc:
        messagebox.showerror('Aperçu indisponible',str(exc),parent=app)
        return False
    dialog=tk.Toplevel(app);dialog.title('Comparer avant / après — page échantillon');dialog.transient(app)
    frame=ttk.Frame(dialog,padding=12);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text=f'Page {page_index+1} — aperçu indicatif : contrôler aussi le PDF final.',wraplength=760).pack(anchor='w',pady=(0,10))
    panels=ttk.Frame(frame);panels.pack(fill='both',expand=True)
    images=[]
    for col,(title,data) in enumerate((('Avant',before),('Après (JPEG 75, 150 dpi cible)',after))):
        pane=ttk.Frame(panels);pane.grid(row=0,column=col,padx=8,sticky='n')
        ttk.Label(pane,text=title).pack()
        im=Image.open(BytesIO(data));im.thumbnail((420,540))
        photo=ImageTk.PhotoImage(im);images.append(photo)
        ttk.Label(pane,image=photo).pack()
    dialog._images=images
    answer={'ok':False}
    def finish(ok):answer['ok']=ok;dialog.destroy()
    actions=ttk.Frame(frame);actions.pack(fill='x',pady=12)
    ttk.Button(actions,text='Annuler',command=lambda:finish(False)).pack(side='right',padx=6)
    ttk.Button(actions,text='Accepter et compresser',command=lambda:finish(True)).pack(side='right')
    dialog.protocol('WM_DELETE_WINDOW',lambda:finish(False));dialog.grab_set();dialog.wait_window()
    return answer['ok']
