"""Canonical desktop UI implementation. Author: Abdelhalim Talbi."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import sys
import os

def _app_version():
    # PyInstaller exposes bundled data via _MEIPASS (onedir and onefile).
    candidates = [Path(getattr(sys, '_MEIPASS', '')) / 'VERSION.txt'] if getattr(sys, '_MEIPASS', None) else []
    candidates.append(Path(__file__).resolve().parents[1] / 'VERSION.txt')
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding='utf-8').strip()
    return 'version inconnue'  # avoid presenting a stale release as current

APP_VERSION = _app_version()
from openpdf_operations import OPERATIONS, run_operation, recover_split
from openpdf_navigation import validate_request, next_page, previous_page, page_window
from openpdf_jobs import JobState


def explain_error(error):
    """Map common exceptions to actionable French messages without hiding details."""
    msg=str(error)
    lower=msg.lower()
    if 'destination existante' in lower or 'file exists' in lower:
        hint='Choisissez un autre nom de fichier ou un dossier de sortie différent.'
    elif 'permission denied' in lower or 'accès refusé' in lower:
        hint='Vérifiez les permissions et fermez les applications qui utilisent ce fichier.'
    elif 'no such file' in lower or 'introuvable' in lower:
        hint='Vérifiez que le document source et le dossier de destination existent.'
    elif 'lock' in lower or 'verrou' in lower:
        hint='Une autre opération utilise cette destination. Réessayez après sa fin.'
    else:
        hint='Vérifiez les paramètres et consultez le journal pour les détails.'
    return f'{hint}\n\nDétail technique : {msg}'

LABELS = dict(zip(OPERATIONS, ('Compresser', 'Fusionner', 'Extraire', 'Découper', 'Réorganiser', 'Rotation', 'OCR', 'Vers Word', 'Vers Excel', 'Vers PowerPoint')))
# Group operations by user intent; keep the stable operation identifiers unchanged.
OPERATION_GROUPS = (
    ('Organiser les pages', ('fusion', 'extraction', 'decoupage', 'reorganisation', 'rotation')),
    ('Optimiser et rechercher', ('compression', 'ocr')),
    ('Convertir en Office', ('docx', 'xlsx', 'pptx')),
)

def suggested_output_name(source, operation):
    """Suggest a filename only; never create or overwrite an output automatically."""
    ext = {'docx': '.docx', 'xlsx': '.xlsx', 'pptx': '.pptx'}.get(operation, '.pdf')
    stem = Path(source).stem if source else 'document'
    suffix = {
        'compression': '_compresse', 'fusion': '_fusion', 'extraction': '_extrait',
        'reorganisation': '_reorganise', 'ocr': '_ocr',
        'docx': '', 'xlsx': '', 'pptx': '',
    }.get(operation, '_resultat')
    return f'{stem}{suffix}{ext}'


def move_selected_source(sources, selected, direction):
    """Return reordered PDF list and selected index; preserve all sources."""
    items=list(sources)
    if direction not in (-1,1):raise ValueError('Direction invalide')
    if not isinstance(selected,int) or not 0 <= selected < len(items):
        return items,selected
    target=selected+direction
    if not 0 <= target < len(items):return items,selected
    items[selected],items[target]=items[target],items[selected]
    return items,target

def validate_page_options(operation, *, first='1', last='1', chunk='1', order='1,2'):
    """Validate operation-specific page options before starting a background job."""
    if operation == 'extraction':
        try:
            start=int(str(first).strip());end=int(str(last).strip())
        except (TypeError,ValueError):
            raise ValueError('Extraction : indiquez des numéros de pages entiers.')
        if start < 1 or end < start:
            raise ValueError('Extraction : la page de début doit être >= 1 et la fin >= au début.')
    elif operation == 'decoupage':
        try: count=int(str(chunk).strip())
        except (TypeError,ValueError):
            raise ValueError('Découpage : indiquez un nombre entier de pages par fichier.')
        if count < 1:raise ValueError('Découpage : au moins une page par fichier.')
    elif operation == 'rotation':
        angle=str(order).strip()
        if angle not in ('90','180','270'):
            raise ValueError('Rotation : choisissez 90, 180 ou 270 degrés.')
    elif operation == 'reorganisation':
        parts=[item.strip() for item in str(order).split(',')]
        if not parts or any(not part or not part.isdecimal() for part in parts):
            raise ValueError('Réorganisation : liste de pages attendue, par exemple 3,1,2.')
        if any(int(part)<1 for part in parts):
            raise ValueError('Réorganisation : les pages commencent à 1.')
    return True

def preview_page_for_source(selected_source, preview_source, preview_page, preview_total):
    """One-based page only when the preview belongs to the selected PDF."""
    if not selected_source or selected_source != preview_source or not isinstance(preview_total,int) or preview_total < 1:
        return None
    if not isinstance(preview_page,int) or not 0 <= preview_page < preview_total:
        return None
    return preview_page+1

def preview_cache_key(source,page):
    """Invalidate rendered pages when the underlying PDF changes on disk."""
    try:
        stat=Path(source).stat()
        return (str(source),int(page),stat.st_size,stat.st_mtime_ns)
    except OSError:
        return (str(source),int(page),None,None)

class OpenPDFStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'OpenPDF Studio V{APP_VERSION} — Abdelhalim Talbi')
        self.geometry('1040x720'); self.minsize(800,560)
        self._job_started=None; self.job_state=JobState();self.sources=[]; self.events=queue.Queue(); self.busy=False; self.preview_page=0; self.preview_total=0; self._preview_source=None; self._preview_loaded_source=None; self._preview_generation=0; self._preview_cache={}; self._preview_pending=set(); self._preview_lock=threading.Lock(); self._preview_inflight=0; self._preview_limit=2
        self.operation=tk.StringVar(value='compression'); self.destination=tk.StringVar()
        self.profile=tk.StringVar(value='smaller_only');self.first=tk.StringVar(value='1');self.last=tk.StringVar(value='1')
        self.chunk=tk.StringVar(value='1');self.order=tk.StringVar(value='1,2');self.rotation=tk.StringVar(value='90');self.language=tk.StringVar(value='fra+eng')
        self._build();self.protocol("WM_DELETE_WINDOW",self._on_close);self.after(100,self._poll)
    def _build(self):
        header=ttk.Frame(self,padding=16);header.pack(fill='x')
        ttk.Label(header,text='OpenPDF Studio',font=('Segoe UI',19,'bold')).pack(side='left')
        ttk.Label(header,text=f'V{APP_VERSION}  •  Espace de travail',font=('Segoe UI',10)).pack(side='right')
        body=ttk.Panedwindow(self,orient='horizontal');body.pack(fill='both',expand=True,padx=14,pady=6)
        left_host=ttk.Frame(body);right=ttk.Frame(body,padding=10)
        body.add(left_host,weight=3);body.add(right,weight=2)
        # Reserve footer/progress space before the scrolling area: controls stay visible
        # even when Windows display scaling leaves very little vertical room.
        footer=ttk.Frame(left_host,padding=8);footer.pack(side='bottom',fill='x')
        self.progress=ttk.Progressbar(left_host,mode='indeterminate');self.progress.pack(side='bottom',fill='x',padx=8)
        scroll_host=ttk.Frame(left_host);scroll_host.pack(fill='both',expand=True)
        canvas=tk.Canvas(scroll_host,highlightthickness=0)
        scrollbar=ttk.Scrollbar(scroll_host,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        left=ttk.Frame(canvas,padding=10)
        window_id=canvas.create_window((0,0),window=left,anchor='nw')
        left.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda event:canvas.itemconfigure(window_id,width=event.width))
        def scroll_form(event):
            # Do not consume wheel events when the form fits; do not overscroll.
            if canvas.bbox('all') is None or canvas.bbox('all')[3] <= canvas.winfo_height():
                return
            if event.delta:
                units = max(1, abs(event.delta) // 120)
                canvas.yview_scroll(-units if event.delta > 0 else units, 'units')
            elif event.num in (4,5):
                canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
        def bind_wheel(widget):
            for event_name in ('<MouseWheel>','<Button-4>','<Button-5>'):
                widget.bind(event_name,scroll_form,add='+')
            for child in widget.winfo_children():bind_wheel(child)
        ttk.Label(left,text='1. Documents PDF',font=('Segoe UI',12,'bold')).pack(anchor='w')
        bar=ttk.Frame(left);bar.pack(fill='x',pady=7)
        self.add_button=ttk.Button(bar,text='Ajouter des PDF',command=self._add);self.add_button.pack(side='left')
        self.remove_button=ttk.Button(bar,text='Retirer',command=self._remove);self.remove_button.pack(side='left',padx=6)
        self.up_button=ttk.Button(bar,text='↑ Monter',command=lambda:self._move_source(-1));self.up_button.pack(side='left',padx=3)
        self.down_button=ttk.Button(bar,text='↓ Descendre',command=lambda:self._move_source(1));self.down_button.pack(side='left',padx=3)
        self.files=tk.Listbox(left,height=7,selectmode='extended',exportselection=False);self.files.pack(fill='x')
        ttk.Label(left,text='2. Opération',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(18,4))
        choices=ttk.Frame(left);choices.pack(fill='x');self.operation_buttons=[]
        self.operation.set('compression')
        for group_name, keys in OPERATION_GROUPS:
            section=ttk.LabelFrame(choices,text=group_name,padding=(8,4))
            section.pack(fill='x',pady=(0,5))
            for column,key in enumerate(keys):
                if key not in LABELS:continue
                button=ttk.Radiobutton(section,text=LABELS[key],variable=self.operation,value=key,command=self._refresh)
                button.grid(row=0,column=column,sticky='w',padx=7,pady=3)
                self.operation_buttons.append(button)
        self.options=ttk.LabelFrame(left,text='Paramètres',padding=10);self.options.pack(fill='x',pady=10)
        self.opts={}
        for name,var in [('Profil',self.profile),('Début',self.first),('Fin',self.last),('Pages par fichier',self.chunk),('Ordre des pages',self.order),('Angle de rotation',self.rotation),('Langue OCR',self.language)]:
            frame=ttk.Frame(self.options);self.opts[name]=frame
            ttk.Label(frame,text=name,width=18).pack(side='left')
            if name=='Profil': ttk.Combobox(frame,textvariable=var,values=('smaller_only','standard','images_balanced'),state='readonly',width=25).pack(side='left')
            elif name=='Angle de rotation': ttk.Combobox(frame,textvariable=var,values=('90','180','270'),state='readonly',width=25).pack(side='left')
            else: ttk.Entry(frame,textvariable=var,width=28).pack(side='left')
        page_actions=ttk.Frame(self.options);page_actions.pack(fill='x',pady=(4,0))
        self.page_start_button=ttk.Button(page_actions,text='Début = page affichée',command=lambda:self._use_preview_page('start'))
        self.page_start_button.pack(side='left',padx=(0,5))
        self.page_end_button=ttk.Button(page_actions,text='Fin = page affichée',command=lambda:self._use_preview_page('end'))
        self.page_end_button.pack(side='left')
        self.page_actions=page_actions
        ttk.Label(left,text='3. Destination',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(12,4))
        dest=ttk.Frame(left);dest.pack(fill='x')
        self.destination_entry=ttk.Entry(dest,textvariable=self.destination);self.destination_entry.pack(side='left',fill='x',expand=True)
        self.browse_button=ttk.Button(dest,text='Parcourir',command=self._browse_destination);self.browse_button.pack(side='left',padx=5)
        self.destination_shortcut=ttk.Button(footer,text='Destination ↓',command=self._focus_destination)
        self.destination_shortcut.pack(side='left',padx=(0,8),pady=4)
        self.go=ttk.Button(footer,text='Exécuter l’opération',command=self._run);self.go.pack(side='right',pady=4)
        self.bind('<Control-o>',lambda event:self._add() if not self.busy else None)
        self.bind('<Control-l>',lambda event:self._focus_destination() if not self.busy else None)
        self.bind('<Control-Return>',lambda event:self._run() if not self.busy else None)
        self.bind('<F6>',lambda event:self._focus_destination() if not self.busy else None)
        self.bind('<Escape>',lambda event:self.focus_set())
        self.operation.trace_add('write',lambda *_:self._on_operation_changed())
        self.recover_button=ttk.Button(footer,text='Récupérer',command=self._recover_dialog);self.recover_button.pack(side='left',pady=4)
        self.audit_button=ttk.Button(footer,text='Audit',command=self._audit_dialog);self.audit_button.pack(side='left',padx=5,pady=4)
        self._form_canvas=canvas
        bind_wheel(left)
        ttk.Label(right,text='Aperçu du document',font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.preview=ttk.Label(right,text='Sélectionnez un document',anchor='center');self.preview.pack(fill='both',expand=True,pady=10)
        nav=ttk.Frame(right);nav.pack(fill='x');ttk.Button(nav,text='◀ Précédente',command=self._prev_page).pack(side='left');self.page_label=ttk.Label(nav,text='Page — / —');self.page_label.pack(side='left',padx=12);ttk.Button(nav,text='Suivante ▶',command=self._next_page).pack(side='left')
        self.files.bind('<<ListboxSelect>>',lambda e:self._select_preview())
        self.files.bind('<Delete>',lambda event:self._remove() if not self.busy else None)
        ttk.Label(right,text='Résultat et journal',font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.log=tk.Text(right,height=8,wrap='word',state='disabled');self.log.pack(fill='x',pady=6)
        self.status=ttk.Label(self,text='Prêt — sélectionnez des PDF, une opération et une destination',padding=(16,6));self.status.pack(anchor='w')
        self.bind('<Control-Shift-O>',lambda event:self._browse_destination() if not self.busy else None)
        self._refresh()
    def _focus_destination(self):
        """Bring output location into view and focus its entry, including at high DPI."""
        if self.busy:
            return
        self.update_idletasks()
        self._form_canvas.yview_moveto(1.0)
        self.destination_entry.focus_set()

    def _set_busy(self, busy):
        self.busy=busy
        state='disabled' if busy else 'normal'
        for widget in (self.go,self.add_button,self.remove_button,self.up_button,self.down_button,self.browse_button,self.recover_button,self.audit_button,self.destination_shortcut,self.page_start_button,self.page_end_button,*self.operation_buttons):
            widget.configure(state=state)
        self.files.configure(state=state)

    def _on_close(self):
        if self.busy:
            messagebox.showwarning('Traitement en cours',
                'Un document est en cours de traitement. Attendez la fin pour éviter une sortie incomplète.',parent=self)
            return
        if getattr(self,'_preview_after_id',None) is not None:
            self.after_cancel(self._preview_after_id)
        self.destroy()

    def _audit_dialog(self):
        """Manage local opt-in audit without showing document names or contents."""
        from openpdf_audit_export_v416 import export_snapshot, verify_snapshot
        window=tk.Toplevel(self)
        window.title('Audit local — confidentialité')
        window.geometry('520x300')
        window.transient(self)
        window.grab_set()
        frame=ttk.Frame(window,padding=16);frame.pack(fill='both',expand=True)
        enabled=tk.BooleanVar(value=os.environ.get('OPENPDF_AUDIT')=='1')
        ttk.Label(frame,text='Audit des opérations',font=('Segoe UI',13,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Sans noms de fichiers, chemins ni contenus PDF.',wraplength=460).pack(anchor='w',pady=8)
        def toggle():
            if enabled.get():
                os.environ['OPENPDF_AUDIT']='1'
            else:
                os.environ.pop('OPENPDF_AUDIT',None)
        ttk.Checkbutton(frame,text='Activer le journal pour cette session',variable=enabled,command=toggle).pack(anchor='w',pady=8)
        def export():
            folder=Path(os.environ.get('OPENPDF_AUDIT_DIR') or Path.home()/'.openpdf-studio')
            source=folder/'operations.jsonl'
            if not source.is_file():
                messagebox.showinfo('Audit','Aucun journal disponible.',parent=window);return
            destination=filedialog.asksaveasfilename(parent=window,title='Exporter le journal',defaultextension='.json',filetypes=[('JSON','*.json')])
            if not destination:return
            try:
                digest=export_snapshot(source,destination)
                messagebox.showinfo('Export terminé',f'Empreinte SHA-256 : {digest}',parent=window)
            except Exception as exc:
                messagebox.showerror('Export impossible',str(exc),parent=window)
        def verify():
            source=filedialog.askopenfilename(parent=window,title='Vérifier un export',filetypes=[('JSON','*.json')])
            if not source:return
            try:
                ok=verify_snapshot(source)
                messagebox.showinfo('Vérification','Empreinte cohérente.' if ok else 'Empreinte incohérente : export modifié.',parent=window)
            except Exception as exc:
                messagebox.showerror('Vérification impossible',str(exc),parent=window)
        buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=12)
        ttk.Button(buttons,text='Exporter',command=export).pack(side='left',padx=(0,8))
        ttk.Button(buttons,text='Vérifier',command=verify).pack(side='left')
        ttk.Label(frame,text='Activation limitée à la session. SHA-256 ne prouve pas l’authenticité.',wraplength=460).pack(anchor='w',pady=8)

    def _recover_dialog(self):
        folder=filedialog.askdirectory(parent=self,title="Dossier à récupérer")
        if not folder:return
        if not messagebox.askyesno("Récupération", "Examiner et nettoyer les transactions interrompues dans ce dossier ?\nLes fichiers non reconnus seront préservés.",parent=self):return
        try:
            report=recover_split(folder)
            details="\n".join(f"{item['stage']}: {item['status']}" for item in report) or "Aucune transaction interrompue"
            messagebox.showinfo("Récupération",details,parent=self)
        except Exception as exc:
            messagebox.showerror("Récupération impossible",str(exc),parent=self)

    def _use_preview_page(self,endpoint):
        if self.busy or self.operation.get()!='extraction':return
        selected=self.files.curselection()
        source=self.sources[selected[0]] if len(selected)==1 else None
        page=preview_page_for_source(source,self._preview_loaded_source,self.preview_page,self.preview_total)
        if page is None:
            messagebox.showinfo('Extraction','Sélectionnez un PDF et attendez que son aperçu soit chargé.',parent=self)
            return
        if endpoint=='start':self.first.set(str(page))
        elif endpoint=='end':self.last.set(str(page))

    def _on_operation_changed(self):
        self._refresh()
        if self.destination.get().strip():
            self.destination.set('')
            self.status.configure(text='Opération modifiée : choisissez une nouvelle destination')
    def _refresh(self):
        key=self.operation.get();show={'compression':('Profil',),'extraction':('Début','Fin'),'decoupage':('Pages par fichier',),'reorganisation':('Ordre des pages',),'rotation':('Angle de rotation',),'ocr':('Langue OCR',)}.get(key,())
        for name,frame in self.opts.items():frame.pack(fill='x',pady=2) if name in show else frame.pack_forget()
        if key=='extraction':self.page_actions.pack(fill='x',pady=(4,0))
        else:self.page_actions.pack_forget()
    def _add(self):
        known={str(Path(p).resolve()).casefold() for p in self.sources}
        for path in filedialog.askopenfilenames(parent=self,filetypes=[('PDF','*.pdf')]):
            normalized=str(Path(path).resolve())
            if normalized.casefold() not in known:
                self.sources.append(normalized);self.files.insert('end',Path(normalized).name)
                known.add(normalized.casefold())
        if self.sources and not self.files.curselection():self.files.selection_set(0)
        self._select_preview()
    def _remove(self):
        for i in reversed(self.files.curselection()):self.files.delete(i);self.sources.pop(i)
        if self.sources:self.files.selection_set(0)
        self._select_preview()
    def _move_source(self,direction):
        selected=self.files.curselection()
        if self.busy or len(selected)!=1:return
        index=selected[0]
        updated,target=move_selected_source(self.sources,index,direction)
        if target==index:return
        self.sources=updated
        self.files.delete(0,'end')
        for path in self.sources:self.files.insert('end',Path(path).name)
        self.files.selection_set(target)
        self.files.see(target)
        self._select_preview()

    def _browse_destination(self):
        if self.operation.get()=='decoupage':p=filedialog.askdirectory(parent=self)
        else:
            ext={'docx':'.docx','xlsx':'.xlsx','pptx':'.pptx'}.get(self.operation.get(),'.pdf')
            suggested = suggested_output_name(self.sources[0] if self.sources else None, self.operation.get())
            p=filedialog.asksaveasfilename(parent=self,defaultextension=ext,
                                           initialfile=suggested,
                                           filetypes=[('Document de sortie',f'*{ext}')])
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
        self._preview_loaded_source=None
        self.preview_total=0
        self.preview.configure(image='',text='Chargement de l’aperçu…');self._photo=None
        idx=self.files.curselection()
        if not idx:
            self.preview_total=0;self.page_label.configure(text='Page — / —');return
        source=self.sources[idx[0]]
        self._preview_generation += 1
        generation=self._preview_generation
        page=self.preview_page
        cache_key=preview_cache_key(source,page)
        if cache_key in self._preview_cache:
            self._show_preview(generation,self._preview_cache[cache_key]);return
        # Debounce fast navigation: only the latest request is dispatched.
        if getattr(self,'_preview_after_id',None) is not None:
            self.after_cancel(self._preview_after_id)
        self._preview_after_id=self.after(120,lambda:self._dispatch_preview(source,page,generation))
    def _dispatch_preview(self,source,page,generation):
        self._preview_after_id=None
        if generation!=self._preview_generation:return
        key=(source,page)
        # A previous worker for this key may belong to an obsolete generation.
        # Do not suppress the current request: stale results are ignored later.
        if (key,generation) in self._preview_pending:return
        self._preview_pending.add((key,generation))
        def worker():
            from openpdf_preview import render_preview
            try: result=render_preview(source,page)
            except Exception as exc: result={'error':str(exc)}
            self.events.put(('preview',generation,result,(key,generation)))
        threading.Thread(target=worker,daemon=True).start()
    def _show_preview(self,generation,result):
        if generation!=self._preview_generation:return
        if 'error' in result:
            self.preview_total=0;self.page_label.configure(text='Page — / —')
            self.preview.configure(text='Aperçu indisponible : '+result['error']);return
        from PIL import Image,ImageTk
        self.preview_total=result['pages'];self.preview_page=result['page']
        self._preview_loaded_source=result['source']
        image=Image.frombytes('RGB',result['size'],result['pixels'])
        self._photo=ImageTk.PhotoImage(image)
        self.preview.configure(image=self._photo,text='')
        self.page_label.configure(text=f'Page {self.preview_page+1} / {self.preview_total}')
        cache_key=preview_cache_key(result['source'],result['page'])
        if len(self._preview_cache)>=12 and cache_key not in self._preview_cache:
            self._preview_cache.pop(next(iter(self._preview_cache)))
        self._preview_cache[cache_key]=result
    def _append(self,text):
        self.log.configure(state='normal');self.log.insert('end',str(text)+'\n');self.log.see('end');self.log.configure(state='disabled')
    def _run(self):
        if self.busy:return
        op=self.operation.get();sources=tuple(self.sources);dest=self.destination.get().strip()
        kwargs=dict(profile=self.profile.get(),first=self.first.get(),last=self.last.get(),chunk=self.chunk.get(),order=self.rotation.get() if op=='rotation' else self.order.get(),language=self.language.get())
        try:
            sources,dest=validate_request(op,sources,dest)
            validate_page_options(op,first=kwargs['first'],last=kwargs['last'],chunk=kwargs['chunk'],order=kwargs['order'])
        except (ValueError,OSError) as exc:
            messagebox.showerror('Paramètres invalides',str(exc),parent=self)
            # Validation failures should guide the user to the field they can fix.
            if 'destination' in str(exc).lower() or 'dossier' in str(exc).lower():
                self._focus_destination()
            return
        job_id=self.job_state.start(op);self._job_started=time.monotonic();self._set_busy(True);self.progress.start(12);self.status.configure(text='Traitement en cours…');self._append(f'Démarrage : {LABELS[op]} — tâche {job_id}')
        def worker():
            try:self.events.put((job_id,'success',run_operation(op,sources,dest,**kwargs)))
            except Exception as exc:self.events.put((job_id,'error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    def _poll(self):
        try:
            while True:
                event=self.events.get_nowait()
                received_id,kind,payload=event[:3]
                if received_id=='preview':
                    if len(event)>3:self._preview_pending.discard(event[3])
                    self._show_preview(kind,payload)
                    continue
                if not self.job_state.finish(received_id,kind):continue
                self._set_busy(False);self.progress.stop();self._job_started=None
                self.status.configure(text='Terminé' if kind=='success' else 'Échec')
                self._append(f'Tâche {received_id} : {payload}')
                if kind=='error':messagebox.showerror('Opération impossible',explain_error(payload),parent=self)
        except queue.Empty:pass
        if self.busy and self._job_started is not None:
            self.status.configure(text=f'Traitement en cours… {int(time.monotonic()-self._job_started)} s (ne pas fermer la fenêtre)')
        self.after(100,self._poll)
if __name__=='__main__':OpenPDFStudio().mainloop()
