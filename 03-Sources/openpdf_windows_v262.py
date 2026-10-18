"""Visual page editor for OpenPDF Studio V26.2. Author: Abdelhalim Talbi."""
import base64
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from openpdf_windows_v260 import OpenPDFApp
from openpdf_core_v261 import page_info, preview_png, edit_pages

class PageEditor(tk.Toplevel):
    def __init__(self, master, source):
        super().__init__(master)
        self.source=source
        self.title('Éditeur de pages — '+Path(source).name)
        self.geometry('1020x760');self.minsize(750,550)
        self.original=page_info(source)
        self.pages=[{'number':x['number'],'rotation':x['rotation']} for x in self.original]
        self.selected=tk.IntVar(value=0)
        self._build();self._redraw()
    def _build(self):
        body=ttk.Frame(self,padding=12);body.pack(fill='both',expand=True)
        left=ttk.Frame(body);left.pack(side='left',fill='y',padx=(0,12))
        ttk.Label(left,text='Pages (ordre de sortie)').pack(anchor='w')
        self.listbox=tk.Listbox(left,width=30,selectmode='extended',exportselection=False)
        self.listbox.pack(fill='both',expand=True,pady=8)
        self.listbox.bind('<<ListboxSelect>>',self._selection_changed)
        actions=ttk.Frame(left);actions.pack(fill='x')
        for label,command in [('Monter',lambda:self.move(-1)),('Descendre',lambda:self.move(1)),('Rotation +90°',lambda:self.rotate(90)),('Rotation -90°',lambda:self.rotate(-90)),('Supprimer',self.delete),('Tout sélectionner',lambda:self.listbox.selection_set(0,'end'))]:
            ttk.Button(actions,text=label,command=command).pack(fill='x',pady=2)
        right=ttk.Frame(body);right.pack(side='left',fill='both',expand=True)
        self.summary=ttk.Label(right,text='');self.summary.pack(anchor='w')
        self.preview=tk.Label(right,bg='#26374d',fg='white',text='Sélectionnez une page')
        self.preview.pack(fill='both',expand=True,pady=8)
        footer=ttk.Frame(right);footer.pack(fill='x')
        ttk.Button(footer,text='Enregistrer sous…',command=self.save).pack(side='right')
        ttk.Button(footer,text='Fermer',command=self.destroy).pack(side='right',padx=8)
    def _redraw(self,selected=None):
        self.listbox.delete(0,'end')
        for i,page in enumerate(self.pages):
            self.listbox.insert('end',f'{i+1:>3}. Page {page["number"]}  ↻ {page["rotation"]}°')
        if self.pages:
            selected=selected if selected is not None else [min(self.selected.get(),len(self.pages)-1)]
            for i in selected:
                if 0<=i<len(self.pages):self.listbox.selection_set(i)
            self.listbox.see(selected[0] if selected else 0)
        self._selection_changed()
    def _selection_changed(self,event=None):
        selected=self.listbox.curselection()
        if not selected:
            self.summary.configure(text=f'{len(self.pages)} page(s) conservée(s)')
            self.preview.configure(image='',text='Sélectionnez une page');self.preview.image=None
            return
        i=selected[0];self.selected.set(i);p=self.pages[i]
        self.summary.configure(text=f'{len(self.pages)} page(s) conservée(s) • Page source {p["number"]} • Rotation {p["rotation"]}°')
        try:
            png=preview_png(self.source,p['number'],550,610)
            photo=tk.PhotoImage(data=base64.b64encode(png).decode('ascii'))
            self.preview.configure(image=photo,text='');self.preview.image=photo
        except Exception as exc:
            self.preview.configure(image='',text=str(exc));self.preview.image=None
    def move(self,delta):
        indices=list(self.listbox.curselection())
        if not indices:return
        # Move the selected group one position without changing its internal order.
        selected=set(indices)
        if delta<0:
            for i in indices:
                if i>0 and i-1 not in selected:
                    self.pages[i-1],self.pages[i]=self.pages[i],self.pages[i-1]
                    selected.remove(i);selected.add(i-1)
        else:
            for i in reversed(indices):
                if i<len(self.pages)-1 and i+1 not in selected:
                    self.pages[i],self.pages[i+1]=self.pages[i+1],self.pages[i]
                    selected.remove(i);selected.add(i+1)
        self._redraw(sorted(selected))
    def rotate(self,angle):
        indices=list(self.listbox.curselection())
        for i in indices:self.pages[i]['rotation']=(self.pages[i]['rotation']+angle)%360
        if indices:self._redraw(indices)
    def delete(self):
        indices=list(self.listbox.curselection())
        if not indices:return
        if len(indices)==len(self.pages):
            messagebox.showwarning('Sélection invalide','Le PDF doit conserver au moins une page.',parent=self);return
        for i in reversed(indices):del self.pages[i]
        self._redraw([min(indices[0],len(self.pages)-1)])
    def save(self):
        if not self.pages:return
        path=filedialog.asksaveasfilename(parent=self,title='Enregistrer le PDF modifié',defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
        if not path:return
        if Path(path).exists() and not messagebox.askyesno('Remplacer le fichier','Remplacer le PDF de destination ?',parent=self):return
        try:
            # Rotations are absolute; the core API accepts final page rotations.
            edit_pages(self.source,path,[p['number'] for p in self.pages],{p['number']:p['rotation'] for p in self.pages})
        except Exception as exc:messagebox.showerror('Échec',str(exc),parent=self);return
        messagebox.showinfo('Enregistrement terminé',f'PDF créé : {path}',parent=self)

class OpenPDFStudio(OpenPDFApp):
    def __init__(self):
        super().__init__();self.title('OpenPDF Studio V26.2 — Abdelhalim Talbi')
    def open_preview(self):
        if self.busy:return
        selection=self.filelist.curselection()
        if not self.files:
            messagebox.showwarning('Aucun PDF','Ajoutez un fichier PDF avant de modifier ses pages.');return
        source=self.files[selection[0]] if selection else self.files[0]
        try:PageEditor(self,source)
        except Exception as exc:messagebox.showerror('Éditeur de pages',str(exc))

if __name__=='__main__':OpenPDFStudio().mainloop()
