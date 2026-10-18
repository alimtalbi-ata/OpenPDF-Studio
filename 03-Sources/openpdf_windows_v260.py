"""OpenPDF Studio desktop shell (Tkinter). Author: Abdelhalim Talbi."""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
from pathlib import Path
from openpdf_core_v261 import page_info,preview_png,edit_pages
from openpdf_core_v260 import merge_pdfs,split_pdf,compress_pdf,extract_text,pdf_to_docx,pdf_to_xlsx,pdf_to_pptx

OPERATIONS={'Fusionner des PDF':merge_pdfs,'Découper en pages':split_pdf,'Compresser / optimiser':compress_pdf,'Extraire le texte':extract_text,'PDF vers Word (texte)':pdf_to_docx,'PDF vers Excel (lignes)':pdf_to_xlsx,'PDF vers PowerPoint (texte)':pdf_to_pptx}
class OpenPDFApp(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('OpenPDF Studio V26.1 — Abdelhalim Talbi'); self.geometry('920x620');self.minsize(760,520)
        self.configure(bg='#101c30'); self.files=[]; self.events=queue.Queue();self.busy=False
        style=ttk.Style(self);style.theme_use('clam');style.configure('TFrame',background='#101c30');style.configure('TLabel',background='#101c30',foreground='#e6efff',font=('Segoe UI',11));style.configure('TButton',padding=9,font=('Segoe UI',10));style.configure('TCombobox',padding=7)
        header=ttk.Frame(self,padding=22);header.pack(fill='x');ttk.Label(header,text='OpenPDF Studio',font=('Segoe UI',23,'bold')).pack(anchor='w');ttk.Label(header,text='Atelier PDF local • aucun document transmis à un serveur').pack(anchor='w')
        # V26.6: redimensionnable workspace avec explorateur latéral.
        self.main_panes=ttk.Panedwindow(self,orient='horizontal')
        self.main_panes.pack(fill='both',expand=True,padx=12,pady=(0,8))
        self.sidebar=ttk.Frame(self.main_panes,padding=8)
        self.main_panes.add(self.sidebar,weight=1)
        ttk.Label(self.sidebar,text='EXPLORATEUR PDF',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,8))
        self.sidebar_files=tk.Listbox(self.sidebar,bg='#1b2c46',fg='#eaf3ff',selectbackground='#3b79b7',relief='flat',exportselection=False)
        self.sidebar_files.pack(fill='both',expand=True)
        self.sidebar_files.bind('<Double-Button-1>',lambda event:self.open_preview())
        self.sidebar_files.bind('<<ListboxSelect>>',self._sidebar_select)
        frame=ttk.Frame(self.main_panes,padding=(12,5,12,12))
        self.main_panes.add(frame,weight=4)
        ttk.Label(frame,text='Opération').pack(anchor='w');self.operation=tk.StringVar(value='Fusionner des PDF');self.combo=ttk.Combobox(frame,textvariable=self.operation,values=list(OPERATIONS),state='readonly');self.combo.pack(fill='x',pady=(4,15));self.combo.bind('<<ComboboxSelected>>',lambda _:self._refresh())
        toolbar=ttk.Frame(frame);toolbar.pack(fill='x');self.add_btn=ttk.Button(toolbar,text='Ajouter des PDF',command=self.add_files);self.add_btn.pack(side='left');self.clear_btn=ttk.Button(toolbar,text='Effacer la liste',command=self.clear_files);self.clear_btn.pack(side='left',padx=8);ttk.Button(toolbar,text='Aperçu / pages',command=self.open_preview).pack(side='left',padx=8);ttk.Button(toolbar,text='Monter',command=lambda:self.move_file(-1)).pack(side='left',padx=3);ttk.Button(toolbar,text='Descendre',command=lambda:self.move_file(1)).pack(side='left',padx=3)
        self.filelist=tk.Listbox(frame,height=8,bg='#1b2c46',fg='#eaf3ff',selectbackground='#3b79b7',font=('Segoe UI',10),relief='flat');self.filelist.pack(fill='both',expand=True,pady=10)
        ttk.Label(frame,text='Sortie (fichier ou dossier pour le découpage)').pack(anchor='w');outrow=ttk.Frame(frame);outrow.pack(fill='x',pady=5);self.destination=tk.StringVar();ttk.Entry(outrow,textvariable=self.destination).pack(side='left',fill='x',expand=True);ttk.Button(outrow,text='Parcourir',command=self.browse_destination).pack(side='left',padx=8)
        self.hint=ttk.Label(frame,text='',wraplength=800);self.hint.pack(anchor='w',pady=5)
        self.progress=ttk.Progressbar(frame,mode='indeterminate');self.progress.pack(fill='x',pady=8);self.run_btn=ttk.Button(frame,text='Exécuter',command=self.run);self.run_btn.pack(anchor='e')
        self.status=tk.StringVar(value='Prêt. Choisissez une opération et ajoutez vos fichiers.');ttk.Label(self,textvariable=self.status,padding=(22,4,22,16),wraplength=850).pack(fill='x')
        self._refresh();self.after(100,self.poll)
    def _refresh(self):
        op=self.operation.get();self.hint.configure(text={'Compresser / optimiser':'Optimisation sans perte du contenu ; une réduction de taille n’est pas garantie.','PDF vers Word (texte)':'Extraction du texte éditable, sans fidélité de mise en page garantie.','PDF vers Excel (lignes)':'Export ligne par ligne, pas de reconstruction fiable des tableaux.','PDF vers PowerPoint (texte)':'Une diapositive par page ; la disposition originale n’est pas conservée.'}.get(op,'Sélectionnez les fichiers dans l’ordre voulu.'))
        self.destination.set('')
    def add_files(self):
        paths=filedialog.askopenfilenames(title='Sélectionner des PDF',filetypes=[('PDF','*.pdf')]);
        if not paths:return
        if self.operation.get()!='Fusionner des PDF':paths=paths[:1];self.files=[]
        self.files.extend(paths);self.filelist.delete(0,'end');self._sync_sidebar()
        for path in self.files:self.filelist.insert('end',path)
    def move_file(self,delta):
        if self.busy:return
        sel=self.filelist.curselection()
        if not sel:return
        i=sel[0];j=i+delta
        if not 0<=j<len(self.files):return
        self.files[i],self.files[j]=self.files[j],self.files[i]
        self.filelist.delete(0,'end')
        for p in self.files:self.filelist.insert('end',p)
        self.filelist.selection_set(j);self._sync_sidebar(select=j)
    def open_preview(self):
        if not self.files or self.busy:return
        source=self.files[0]
        try:info=page_info(source)
        except Exception as exc:messagebox.showerror('Aperçu',str(exc));return
        win=tk.Toplevel(self);win.title('Aperçu des pages — '+Path(source).name);win.geometry('740x820')
        panel=ttk.Frame(win,padding=10);panel.pack(fill='both',expand=True)
        row=ttk.Frame(panel);row.pack(fill='x')
        current=tk.IntVar(value=1);image=tk.Label(panel,bg='#29384c');image.pack(fill='both',expand=True,pady=8)
        label=ttk.Label(row,text='');label.pack(side='left',padx=10)
        def render():
            n=current.get()
            try:
                import base64
                png=preview_png(source,n,600,650)
                photo=tk.PhotoImage(data=base64.b64encode(png).decode('ascii'))
                image.configure(image=photo,text='');image.image=photo
                label.configure(text=f'Page {n}/{len(info)} • {info[n-1]["width"]}×{info[n-1]["height"]} pt')
            except Exception as exc:image.configure(text=str(exc),image='');image.image=None
        def advance(d):current.set(max(1,min(len(info),current.get()+d)));render()
        ttk.Button(row,text='◀ Précédente',command=lambda:advance(-1)).pack(side='left')
        ttk.Button(row,text='Suivante ▶',command=lambda:advance(1)).pack(side='left',padx=8)
        render()
    def clear_files(self):self.files=[];self.filelist.delete(0,'end');self._sync_sidebar()
    def _sync_sidebar(self,select=None):
        if not hasattr(self,'sidebar_files'):return
        self.sidebar_files.delete(0,'end')
        for path in self.files:self.sidebar_files.insert('end',Path(path).name)
        if select is not None and 0<=select<len(self.files):self.sidebar_files.selection_set(select)
    def _sidebar_select(self,event=None):
        selection=self.sidebar_files.curselection()
        if not selection:return
        self.filelist.selection_clear(0,'end')
        self.filelist.selection_set(selection[0])
        self.filelist.see(selection[0])
        # V26.5 binds the primary list to its properties panel.
        self.filelist.event_generate('<<ListboxSelect>>')
    def browse_destination(self):
        op=self.operation.get()
        if op=='Découper en pages':path=filedialog.askdirectory(title='Dossier de destination')
        else:
            ext='.docx' if 'Word' in op else '.xlsx' if 'Excel' in op else '.pptx' if 'PowerPoint' in op else '.txt' if 'texte' in op else '.pdf'
            path=filedialog.asksaveasfilename(defaultextension=ext,filetypes=[(ext.upper(),'*'+ext)],title='Enregistrer sous')
        if path:self.destination.set(path)
    def run(self):
        if self.busy:return
        op=self.operation.get();files=self.files.copy();dest=self.destination.get().strip()
        if not files or not dest:messagebox.showwarning('Fichiers manquants','Ajoutez un PDF et choisissez la destination.');return
        if op!='Fusionner des PDF' and len(files)!=1:messagebox.showwarning('Sélection','Cette opération nécessite un seul PDF.');return
        if Path(dest).exists() and op!='Découper en pages' and not messagebox.askyesno('Confirmer','Remplacer le fichier de sortie existant ?'):return
        self.busy=True;self.run_btn.state(['disabled']);self.add_btn.state(['disabled']);self.clear_btn.state(['disabled']);self.progress.start(12);self.status.set('Traitement en cours…')
        def work():
            try:
                func=OPERATIONS[op];result=func(files,dest) if op=='Fusionner des PDF' else func(files[0],dest)
                self.events.put(('ok',result))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=work,daemon=True).start()
    def poll(self):
        try:
            kind,payload=self.events.get_nowait();self.busy=False;self.progress.stop()
            for b in (self.run_btn,self.add_btn,self.clear_btn):b.state(['!disabled'])
            if kind=='ok':self.status.set(f'Terminé : {len(payload)} fichier(s) créé(s).');messagebox.showinfo('Opération terminée',self.status.get())
            else:self.status.set('Échec : '+payload);messagebox.showerror('Erreur',payload)
        except queue.Empty:pass
        self.after(100,self.poll)
if __name__=='__main__':OpenPDFApp().mainloop()
