"""V32.6 : comparaison visuelle d'une page, sans altérer la source. Abdelhalim Talbi."""
from pathlib import Path
import tempfile

def render_comparison(source, page_index=0, *, dpi=100, quality=75):
    """Return two PNG byte strings (original, compressed candidate), page sample only.

    The source is never changed. A full document must still be checked separately.
    """
    import fitz
    from openpdf_compression_v325 import compress_images
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

def preview_dialog(app, source, *, page_index=0, render=render_comparison):
    """Navigable page comparison, on-demand rendering, zoom and explicit consent."""
    import tkinter as tk
    from tkinter import ttk, messagebox
    from io import BytesIO
    import fitz
    from PIL import Image, ImageTk
    try:
        with fitz.open(str(source)) as document:
            if document.needs_pass: raise ValueError('PDF protégé')
            total = len(document)
        if total < 1: raise ValueError('PDF vide')
    except Exception as exc:
        messagebox.showerror('Aperçu indisponible',str(exc),parent=app)
        return False
    dialog=tk.Toplevel(app)
    dialog.title('Comparer avant / après — navigation multipage')
    dialog.transient(app)
    dialog.geometry('1000x720')
    frame=ttk.Frame(dialog,padding=12);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Prévisualisation indicative — contrôlez le PDF complet après compression.',wraplength=950).pack(anchor='w')
    nav=ttk.Frame(frame);nav.pack(fill='x',pady=8)
    page=tk.IntVar(value=max(0,min(page_index,total-1)))
    zoom=tk.IntVar(value=100)
    status=tk.StringVar(value='')
    ttk.Label(nav,textvariable=status).pack(side='left',padx=12)
    panels=ttk.Frame(frame);panels.pack(fill='both',expand=True)
    panels.columnconfigure(0,weight=1);panels.columnconfigure(1,weight=1)
    views=[]
    for column,title in enumerate(('Original','Candidat recompressé (JPEG 75, cible 150 dpi)')):
        pane=ttk.Frame(panels);pane.grid(row=0,column=column,sticky='nsew',padx=5)
        ttk.Label(pane,text=title).pack()
        image=ttk.Label(pane,anchor='center');image.pack(fill='both',expand=True)
        views.append(image)
    cache={}
    def redraw():
        index=page.get();level=zoom.get()
        status.set(f'Page {index+1} / {total}  |  Zoom {level}%')
        try:
            if index not in cache:
                # Cache limited to two pages to bound memory use.
                if len(cache)>=2:cache.pop(next(iter(cache)))
                cache[index]=render(source,index)
            for view,data in zip(views,cache[index]):
                img=Image.open(BytesIO(data));img.thumbnail((int(450*level/100),int(560*level/100)))
                photo=ImageTk.PhotoImage(img)
                view.configure(image=photo,text='');view.image=photo
        except Exception as exc:
            for view in views:view.configure(image='',text='Aperçu indisponible');view.image=None
            messagebox.showerror('Erreur de rendu',str(exc),parent=dialog)
            return False
        return True
    def move(delta):
        next_page=max(0,min(total-1,page.get()+delta))
        if next_page!=page.get():page.set(next_page);redraw()
    ttk.Button(nav,text='◀ Précédente',command=lambda:move(-1)).pack(side='left',padx=3)
    ttk.Button(nav,text='Suivante ▶',command=lambda:move(1)).pack(side='left',padx=3)
    ttk.Label(nav,text='Zoom').pack(side='left',padx=(18,4))
    for value in (75,100,150):
        ttk.Button(nav,text=f'{value} %',command=lambda v=value:(zoom.set(v),redraw())).pack(side='left',padx=2)
    answer={'ok':False}
    def finish(value):answer['ok']=value;dialog.destroy()
    actions=ttk.Frame(frame);actions.pack(fill='x',pady=8)
    ttk.Button(actions,text='Annuler',command=lambda:finish(False)).pack(side='right',padx=6)
    ttk.Button(actions,text='Accepter et compresser',command=lambda:finish(True)).pack(side='right')
    dialog.protocol('WM_DELETE_WINDOW',lambda:finish(False))
    if not redraw():dialog.destroy();return False
    dialog.grab_set();dialog.wait_window()
    return answer['ok']
