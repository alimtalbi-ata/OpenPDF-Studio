"""Modern workspace V35.1. Author: Abdelhalim Talbi."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from openpdf_ui_controller_v348 import OPERATIONS, run_operation
from openpdf_workspace_v349 import validate_request, next_page, previous_page, page_window
from openpdf_job_controller_v350 import JobState

LABELS = dict(zip(OPERATIONS, ('Compresser', 'Fusionner', 'Extraire', 'Découper', 'Réorganiser', 'OCR', 'Vers Word', 'Vers Excel', 'Vers PowerPoint')))
class OpenPDFStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V35.1 — Abdelhalim Talbi')
        self.geometry('1040x720'); self.minsize(800,560)
        self.job_state=JobState();self.sources=[]; self.events=queue.Queue(); self.busy=False; self.preview_page=0; self.preview_total=0; self._preview_source=None
        self.operation=tk.StringVar(value='compression'); self.destination=tk.StringVar()
        self.profile=tk.StringVar(value='smaller_only');self.first=tk.StringVar(value='1');self.last=tk.StringVar(value='1')
        self.chunk=tk.StringVar(value='1');self.order=tk.StringVar(value='1,2');self.language=tk.StringVar(value='fra+eng')
        self._build();self.after(100,self._poll)
    def _build(self):
        header=ttk.Frame(self,padding=16);header.pack(fill='x')
        ttk.Label(header,text='OpenPDF Studio',font=('Segoe UI',19,'bold')).pack(side='left')
        ttk.Label(header,text='V35.1  •  Espace de travail',font=('Segoe UI',10)).pack(side='right')
        body=ttk.Panedwindow(self,orient='horizontal');body.pack(fill='both',expand=True,padx=14,pady=6)
        left=ttk.Frame(body,padding=10);right=ttk.Frame(body,padding=10)
        body.add(left,weight=3);body.add(right,weight=2)
        ttk.Label(left,text='1. Documents PDF',font=('Segoe UI',12,'bold')).pack(anchor='w')
        bar=ttk.Frame(left);bar.pack(fill='x',pady=7)
        ttk.Button(bar,text='Ajouter des PDF',command=self._add).pack(side='left')
        ttk.Button(bar,text='Retirer',command=self._remove).pack(side='left',padx=6)
        self.files=tk.Listbox(left,height=7,selectmode='extended');self.files.pack(fill='x')
        ttk.Label(left,text='2. Opération',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(18,4))
        choices=ttk.Frame(left);choices.pack(fill='x')
        for i,(key,label) in enumerate(LABELS.items()):
            ttk.Radiobutton(choices,text=label,variable=self.operation,value=key,command=self._refresh).grid(row=i//3,column=i%3,sticky='w',padx=8,pady=5)
        self.options=ttk.LabelFrame(left,text='Paramètres',padding=10);self.options.pack(fill='x',pady=10)
        self.opts={}
        for name,var in [('Profil',self.profile),('Début',self.first),('Fin',self.last),('Pages par fichier',self.chunk),('Ordre des pages',self.order),('Langue OCR',self.language)]:
            frame=ttk.Frame(self.options);self.opts[name]=frame
            ttk.Label(frame,text=name,width=18).pack(side='left')
            if name=='Profil': ttk.Combobox(frame,textvariable=var,values=('smaller_only','standard','images_balanced'),state='readonly',width=25).pack(side='left')
            else: ttk.Entry(frame,textvariable=var,width=28).pack(side='left')
        ttk.Label(left,text='3. Destination',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(12,4))
        dest=ttk.Frame(left);dest.pack(fill='x')
        ttk.Entry(dest,textvariable=self.destination).pack(side='left',fill='x',expand=True)
        ttk.Button(dest,text='Parcourir',command=self._browse_destination).pack(side='left',padx=5)
        self.go=ttk.Button(left,text='Exécuter',command=self._run);self.go.pack(anchor='e',pady=14)
        self.progress=ttk.Progressbar(left,mode='indeterminate');self.progress.pack(fill='x',pady=(0,8))
        ttk.Label(right,text='Aperçu du document',font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.preview=ttk.Label(right,text='Sélectionnez un document',anchor='center');self.preview.pack(fill='both',expand=True,pady=10)
        nav=ttk.Frame(right);nav.pack(fill='x');ttk.Button(nav,text='◀ Précédente',command=self._prev_page).pack(side='left');self.page_label=ttk.Label(nav,text='Page — / —');self.page_label.pack(side='left',padx=12);ttk.Button(nav,text='Suivante ▶',command=self._next_page).pack(side='left')
        self.files.bind('<<ListboxSelect>>',lambda e:self._select_preview())
        ttk.Label(right,text='Résultat et journal',font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.log=tk.Text(right,height=8,wrap='word',state='disabled');self.log.pack(fill='x',pady=6)
        self.status=ttk.Label(self,text='Prêt',padding=(16,6));self.status.pack(anchor='w')
        self._refresh()
    def _refresh(self):
        key=self.operation.get();show={'compression':('Profil',),'extraction':('Début','Fin'),'decoupage':('Pages par fichier',),'reorganisation':('Ordre des pages',),'ocr':('Langue OCR',)}.get(key,())
        for name,frame in self.opts.items():frame.pack(fill='x',pady=2) if name in show else frame.pack_forget()
    def _add(self):
        for path in filedialog.askopenfilenames(parent=self,filetypes=[('PDF','*.pdf')]):
            if path not in self.sources:self.sources.append(path);self.files.insert('end',Path(path).name)
        self._select_preview()
    def _remove(self):
        for i in reversed(self.files.curselection()):self.files.delete(i);self.sources.pop(i)
        self._select_preview()
    def _browse_destination(self):
        if self.operation.get()=='decoupage':p=filedialog.askdirectory(parent=self)
        else:
            ext={'docx':'.docx','xlsx':'.xlsx','pptx':'.pptx'}.get(self.operation.get(),'.pdf')
            p=filedialog.asksaveasfilename(parent=self,defaultextension=ext,filetypes=[('Document de sortie',f'*{ext}')])
        if p:self.destination.set(p)
    def _select_preview(self):
        idx=self.files.curselection()
        source=self.sources[idx[0]] if idx else None
        if source != self._preview_source:
            self._preview_source=source;self.preview_page=0
        self._preview()
    def _next_page(self):
        if self.preview_total:self.preview_page=next_page(self.preview_page,self.preview_total);self._preview()
    def _prev_page(self):
        if self.preview_total:self.preview_page=previous_page(self.preview_page,self.preview_total);self._preview()
    def _preview(self):
        self.preview.configure(image='',text='Aucun aperçu');self._photo=None
        idx=self.files.curselection()
        if not idx:
            self.preview_total=0;self.page_label.configure(text='Page — / —');return
        try:
            import fitz
            from PIL import Image,ImageTk
            with fitz.open(self.sources[idx[0]]) as doc:
                if not doc.page_count or doc.needs_pass:raise ValueError('PDF vide ou protégé')
                self.preview_total=doc.page_count
                self.preview_page=page_window(self.preview_page,self.preview_total)
                pix=doc[self.preview_page].get_pixmap(matrix=fitz.Matrix(0.65,0.65),alpha=False)
                im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                im.thumbnail((360,390));self._photo=ImageTk.PhotoImage(im)
                self.preview.configure(image=self._photo,text='')
                self.page_label.configure(text=f'Page {self.preview_page+1} / {self.preview_total}')
        except Exception as exc:
            self.preview_total=0;self.page_label.configure(text='Page — / —')
            self.preview.configure(text=f'Aperçu indisponible : {exc}')
    def _append(self,text):
        self.log.configure(state='normal');self.log.insert('end',str(text)+'\n');self.log.see('end');self.log.configure(state='disabled')
    def _run(self):
        if self.busy:return
        op=self.operation.get();sources=tuple(self.sources);dest=self.destination.get().strip()
        kwargs=dict(profile=self.profile.get(),first=self.first.get(),last=self.last.get(),chunk=self.chunk.get(),order=self.order.get(),language=self.language.get())
        try:
            sources,dest=validate_request(op,sources,dest)
        except (ValueError,OSError) as exc:
            messagebox.showerror('Paramètres invalides',str(exc),parent=self);return
        job_id=self.job_state.start(op);self.busy=True;self.go.configure(state='disabled');self.progress.start(12);self.status.configure(text='Traitement en cours…');self._append(f'Démarrage : {LABELS[op]} — tâche {job_id}')
        def worker():
            try:self.events.put((job_id,'success',run_operation(op,sources,dest,**kwargs)))
            except Exception as exc:self.events.put((job_id,'error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    def _poll(self):
        try:
            while True:
                received_id,kind,payload=self.events.get_nowait()
                if not self.job_state.finish(received_id,kind):continue
                self.busy=False;self.go.configure(state='normal');self.progress.stop()
                self.status.configure(text='Terminé' if kind=='success' else 'Échec')
                self._append(f'Tâche {received_id} : {payload}')
                if kind=='error':messagebox.showerror('Opération impossible',str(payload),parent=self)
        except queue.Empty:pass
        self.after(100,self._poll)
if __name__=='__main__':OpenPDFStudio().mainloop()
