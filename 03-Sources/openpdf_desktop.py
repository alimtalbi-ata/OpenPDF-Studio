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
from openpdf_ui_controller_v348 import OCR_MODES
from openpdf_compression_ui_v471 import QUALITY_MODES
from openpdf_compression_result_v490 import format_compression_result
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

LABELS = dict(zip(OPERATIONS, ('Compresser', 'Fusionner', 'Extraire', 'Découper', 'Réorganiser', 'OCR', 'Vers Word', 'Vers Excel', 'Vers PowerPoint')))
# Group operations by user intent; keep the stable operation identifiers unchanged.
OPERATION_GROUPS = (
    ('Organiser les pages', ('fusion', 'extraction', 'decoupage', 'reorganisation')),
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


class OpenPDFStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f'OpenPDF Studio V{APP_VERSION} — Abdelhalim Talbi')
        self.geometry('1040x720'); self.minsize(800,560)
        self._job_started=None; self.job_state=JobState();self.sources=[]; self.events=queue.Queue(); self.busy=False; self.preview_page=0; self.preview_total=0; self._preview_source=None; self._preview_generation=0; self._preview_cache={}; self._preview_pending=set(); self._preview_lock=threading.Lock(); self._preview_inflight=0; self._preview_limit=2
        self.operation=tk.StringVar(value='compression'); self.destination=tk.StringVar()
        self.profile=tk.StringVar(value='smaller_only');self.first=tk.StringVar(value='1');self.last=tk.StringVar(value='1')
        self.chunk=tk.StringVar(value='1');self.order=tk.StringVar(value='1,2');self.extraction_selection=tk.StringVar(value='');self.language=tk.StringVar(value='fra+eng')
        self.ocr_mode=tk.StringVar(value='Pages sans texte')
        self.ocr_before_office=tk.BooleanVar(value=False)  # explicit consent; never OCR silently
        self.xlsx_tables=tk.BooleanVar(value=False)  # explicit opt-in; preserve legacy Excel by default
        self.deskew_angle=tk.StringVar(value='0')  # V534: manual correction of tilted scans
        self.auto_deskew=tk.BooleanVar(value=False)  # V535: opt-in conservative estimation
        self.min_ocr_table_cells=tk.StringVar(value='0')  # 0 disables the strict occupancy gate
        self.compression_quality=tk.StringVar(value=QUALITY_MODES[0])
        self.full_rgb_audit=tk.BooleanVar(value=False)  # V49.0 opt-in, not a default guarantee
        self._build();self.protocol("WM_DELETE_WINDOW",self._on_close);self.after(100,self._poll)
    def _build(self):
        header=ttk.Frame(self,padding=16);header.pack(fill='x')
        ttk.Label(header,text='OpenPDF Studio',font=('Segoe UI',19,'bold')).pack(side='left')
        ttk.Label(header,text=f'V{APP_VERSION}  •  Espace de travail',font=('Segoe UI',10)).pack(side='right')
        self.ocr_quality_button=ttk.Button(header,text='Qualité OCR',command=self._ocr_quality_dialog);self.ocr_quality_button.pack(side='right',padx=5)
        self.office_quality_button=ttk.Button(header,text='Qualité Office',command=self._office_quality_dialog);self.office_quality_button.pack(side='right',padx=5)
        self.audit_button=ttk.Button(header,text='Audit',command=self._audit_dialog);self.audit_button.pack(side='right',padx=5)
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
                button.grid(row=column//2,column=column%2,sticky='w',padx=7,pady=3)
                self.operation_buttons.append(button)
        self.options=ttk.LabelFrame(left,text='Paramètres',padding=10);self.options.pack(fill='x',pady=10)
        self.opts={}
        for name,var in [('Profil',self.profile),('Début',self.first),('Fin',self.last),('Pages par fichier',self.chunk),('Ordre des pages',self.order),('Pages à extraire',self.extraction_selection),('Langue OCR',self.language),('Mode OCR',self.ocr_mode),('OCR avant conversion',self.ocr_before_office),('Tableaux Excel éditables',self.xlsx_tables),('Cellules OCR min/page',self.min_ocr_table_cells),('Redresser scan (degrés)',self.deskew_angle),('Redressement automatique',self.auto_deskew),('Contrôle qualité',self.compression_quality),('Audit RGB intégral',self.full_rgb_audit)]:
            frame=ttk.Frame(self.options);self.opts[name]=frame
            if name not in ('OCR avant conversion','Tableaux Excel éditables'):
                ttk.Label(frame,text=('Ordre (ex. toutes,!paires)' if name=='Ordre des pages' else 'Pages (optionnel, ex. !paires)' if name=='Pages à extraire' else name),width=22).pack(side='left')
            if name=='Profil': ttk.Combobox(frame,textvariable=var,values=('smaller_only','standard','images_balanced'),state='readonly',width=25).pack(side='left')
            elif name=='Contrôle qualité': ttk.Combobox(frame,textvariable=var,values=QUALITY_MODES,state='readonly',width=27).pack(side='left')
            elif name=='Audit RGB intégral': ttk.Checkbutton(frame,variable=var,text='Tous les pixels à 50 % (plus lent, seuil 2 %)').pack(side='left')
            elif name=='Mode OCR': ttk.Combobox(frame,textvariable=var,values=tuple(OCR_MODES),state='readonly',width=28).pack(side='left')
            elif name=='Tableaux Excel éditables':
                self.xlsx_tables_check=ttk.Checkbutton(frame,variable=var,command=self._refresh,text='Tableaux en feuilles Excel éditables (OCR : vérifier les valeurs)')
                self.xlsx_tables_check.pack(side='left')
            elif name=='Redressement automatique':
                ttk.Checkbutton(frame,variable=var,
                    text='Auto (prudent, scans uniquement ; aucune garantie OCR)').pack(side='left')
            elif name=='OCR avant conversion':
                self.ocr_office_check=ttk.Checkbutton(frame,variable=var,command=self._refresh,text='OCR si PDF numérisé (fidélité limitée)')
                self.ocr_office_check.pack(side='left')
            else: ttk.Entry(frame,textvariable=var,width=28).pack(side='left')
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
        for widget in (self.go,self.add_button,self.remove_button,self.browse_button,self.recover_button,self.audit_button,self.ocr_quality_button,self.office_quality_button,self.destination_shortcut,self.ocr_office_check,self.xlsx_tables_check,*self.operation_buttons):
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

    def _ocr_quality_dialog(self):
        """Opt-in OCR corpus quality check; never show extracted text or source names."""
        if self.busy:
            return
        from openpdf_ocr_quality_ui_v541 import (safe_receipt,
            format_ocr_quality_summary, serialize_ocr_quality_receipt)
        window = tk.Toplevel(self)
        window.title('Qualité OCR — références indépendantes')
        window.geometry('620x440')
        window.transient(self)
        frame = ttk.Frame(window, padding=16); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Qualification OCR sur corpus annoté',
                  font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        ttk.Label(frame, text=('Compare la couche texte des PDF à des références locales. '
                  'Ne mesure ni la fidélité visuelle ni la qualité des conversions Office.'),
                  wraplength=570).pack(anchor='w', pady=8)
        manifest = tk.StringVar()
        selection = ttk.Frame(frame); selection.pack(fill='x', pady=6)
        ttk.Entry(selection, textvariable=manifest).pack(side='left', fill='x', expand=True)
        def browse():
            selected = filedialog.askopenfilename(parent=window,
                title='Manifeste du corpus OCR', filetypes=[('JSON', '*.json')])
            if selected:
                manifest.set(selected)
        browse_button = ttk.Button(selection, text='Manifeste…', command=browse)
        browse_button.pack(side='left', padx=6)
        output = tk.Text(frame, height=12, wrap='word', state='disabled')
        output.pack(fill='both', expand=True, pady=8)
        actions = ttk.Frame(frame); actions.pack(fill='x')
        result_holder = {'report': None}
        replies = queue.Queue()
        def show(message):
            output.configure(state='normal')
            output.delete('1.0', 'end')
            output.insert('end', message)
            output.configure(state='disabled')
        def export():
            report = result_holder['report']
            if report is None:
                return
            destination = filedialog.asksaveasfilename(parent=window,
                title='Exporter le reçu de qualification', defaultextension='.json',
                filetypes=[('JSON', '*.json')])
            if not destination:
                return
            try:
                # Exclusive create: no overwrite, including pre-existing symlinks.
                with Path(destination).open('x', encoding='utf-8') as stream:
                    stream.write(serialize_ocr_quality_receipt(report))
                messagebox.showinfo('Qualité OCR', 'Reçu JSON enregistré sans contenu PDF.', parent=window)
            except (ValueError, OSError):
                messagebox.showerror('Export refusé',
                    'Destination déjà existante ou non accessible.', parent=window)
        export_button = ttk.Button(actions, text='Exporter le reçu', command=export,
                                   state='disabled')
        export_button.pack(side='right')
        def poll():
            if not window.winfo_exists():
                return
            try:
                status, payload = replies.get_nowait()
            except queue.Empty:
                window.after(100, poll)
                return
            browse_button.configure(state='normal')
            run_button.configure(state='normal')
            if status == 'success':
                result_holder['report'] = payload
                show(format_ocr_quality_summary(payload))
                export_button.configure(state='normal')
            else:
                show('Qualification impossible : preuve invalide, illisible ou incomplète. '
                     'Consultez le manifeste local. Aucun texte PDF affiché.')
        def run():
            selected = manifest.get().strip()
            if not selected:
                messagebox.showwarning('Qualité OCR', 'Choisissez un manifeste JSON.', parent=window)
                return
            result_holder['report'] = None
            export_button.configure(state='disabled')
            run_button.configure(state='disabled')
            browse_button.configure(state='disabled')
            show('Analyse locale en cours…')
            def worker():
                try:
                    from openpdf_ocr_reference_corpus_v539 import evaluate_ocr_reference_corpus
                    result = safe_receipt(evaluate_ocr_reference_corpus(selected))
                    replies.put(('success', result))
                except (ValueError, OSError, RuntimeError, TypeError, ImportError):
                    replies.put(('error', None))
            threading.Thread(target=worker, daemon=True).start()
            window.after(100, poll)
        run_button = ttk.Button(actions, text='Analyser', command=run)
        run_button.pack(side='left')

    def _office_quality_dialog(self):
        """V543: opt-in, asynchronous, privacy-preserving editable Office audit."""
        if self.busy:
            return
        from openpdf_office_precision_order_ui_v544 import (
            safe_office_receipt, format_office_quality_summary,
            serialize_office_quality_receipt)
        window = tk.Toplevel(self)
        window.title('Qualité Office — références indépendantes')
        window.geometry('650x500')
        window.transient(self)
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Qualification Word / Excel / PowerPoint éditables',
                  font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        ttk.Label(frame, text=('Compare les objets éditables DOCX, XLSX et PPTX à un corpus annoté. '
                  'Avec les seuils V544, mesure aussi la précision et l’ordre d’extraction des tokens. '
                  'Cela ne prouve pas l’ordre de lecture visuel ni la fidélité graphique.'),
                  wraplength=600).pack(anchor='w', pady=8)
        manifest = tk.StringVar()
        selection = ttk.Frame(frame); selection.pack(fill='x', pady=6)
        entry = ttk.Entry(selection, textvariable=manifest)
        entry.pack(side='left', fill='x', expand=True)
        def browse():
            selected = filedialog.askopenfilename(parent=window,
                title='Manifeste du corpus Office', filetypes=[('JSON', '*.json')])
            if selected:
                manifest.set(selected)
        browse_button = ttk.Button(selection, text='Manifeste…', command=browse)
        browse_button.pack(side='left', padx=6)
        output = tk.Text(frame, height=13, wrap='word', state='disabled')
        output.pack(fill='both', expand=True, pady=8)
        actions = ttk.Frame(frame); actions.pack(fill='x')
        result_holder = {'report': None}
        replies = queue.Queue()
        def show(message):
            output.configure(state='normal')
            output.delete('1.0', 'end')
            output.insert('end', message)
            output.configure(state='disabled')
        def export():
            report = result_holder['report']
            if report is None:
                return
            destination = filedialog.asksaveasfilename(parent=window,
                title='Exporter le reçu Office', defaultextension='.json',
                filetypes=[('JSON', '*.json')])
            if not destination:
                return
            try:
                # Exclusive create: never overwrite files or symlinks.
                with Path(destination).open('x', encoding='utf-8') as stream:
                    stream.write(serialize_office_quality_receipt(report))
                messagebox.showinfo('Qualité Office', 'Reçu privé exporté.', parent=window)
            except (ValueError, OSError):
                messagebox.showerror('Export refusé',
                    'Destination déjà existante ou non accessible.', parent=window)
        export_button = ttk.Button(actions, text='Exporter le reçu', command=export,
                                   state='disabled')
        export_button.pack(side='right')
        def poll():
            if not window.winfo_exists():
                return
            try:
                status, payload = replies.get_nowait()
            except queue.Empty:
                window.after(100, poll)
                return
            browse_button.configure(state='normal')
            run_button.configure(state='normal')
            entry.configure(state='normal')
            if status == 'success':
                result_holder['report'] = payload
                show(format_office_quality_summary(payload))
                export_button.configure(state='normal')
            else:
                show('Qualification impossible : preuve invalide ou incomplète. '
                     'Aucun texte, nom de fichier ou chemin du corpus n’est affiché.')
        def run():
            selected = manifest.get().strip()
            if not selected:
                messagebox.showwarning('Qualité Office', 'Choisissez un manifeste JSON.', parent=window)
                return
            result_holder['report'] = None
            export_button.configure(state='disabled')
            run_button.configure(state='disabled')
            browse_button.configure(state='disabled')
            entry.configure(state='disabled')
            show('Qualification locale en cours…')
            def worker():
                try:
                    from openpdf_office_reference_v542 import evaluate_office_reference_corpus
                    result = safe_office_receipt(evaluate_office_reference_corpus(selected))
                    replies.put(('success', result))
                except Exception:
                    # Avoid leaking paths/text from library exception messages.
                    replies.put(('error', None))
            threading.Thread(target=worker, daemon=True).start()
            window.after(100, poll)
        run_button = ttk.Button(actions, text='Analyser', command=run)
        run_button.pack(side='left')

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

    def _on_operation_changed(self):
        self._refresh()
        if self.destination.get().strip():
            self.destination.set('')
            self.status.configure(text='Opération modifiée : choisissez une nouvelle destination')
    def _refresh(self):
        key=self.operation.get();show={'compression':('Profil','Contrôle qualité','Audit RGB intégral'),'extraction':('Début','Fin','Pages à extraire'),'decoupage':('Pages par fichier',),'reorganisation':('Ordre des pages',),'ocr':('Langue OCR','Mode OCR'),'docx':('Langue OCR','OCR avant conversion'),'xlsx':('Langue OCR','OCR avant conversion','Tableaux Excel éditables'),'pptx':('Langue OCR','OCR avant conversion')}.get(key,())
        if key in ('docx', 'xlsx', 'pptx') and self.ocr_before_office.get():
            show += ('Redresser scan (degrés)',)
            show += ('Redressement automatique',)
        if key == 'xlsx' and self.ocr_before_office.get() and self.xlsx_tables.get():
            show += ('Cellules OCR min/page',)
        for name,frame in self.opts.items():frame.pack(fill='x',pady=2) if name in show else frame.pack_forget()
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
        self.preview.configure(image='',text='Chargement de l’aperçu…');self._photo=None
        idx=self.files.curselection()
        if not idx:
            self.preview_total=0;self.page_label.configure(text='Page — / —');return
        source=self.sources[idx[0]]
        self._preview_generation += 1
        generation=self._preview_generation
        page=self.preview_page
        cache_key=(source,page)
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
        if key in self._preview_pending:return
        self._preview_pending.add(key)
        def worker():
            from openpdf_preview import render_preview
            try: result=render_preview(source,page)
            except Exception as exc: result={'error':str(exc)}
            self.events.put(('preview',generation,result,key))
        threading.Thread(target=worker,daemon=True).start()
    def _show_preview(self,generation,result):
        if generation!=self._preview_generation:return
        if 'error' in result:
            self.preview_total=0;self.page_label.configure(text='Page — / —')
            self.preview.configure(text='Aperçu indisponible : '+result['error']);return
        from PIL import Image,ImageTk
        self.preview_total=result['pages'];self.preview_page=result['page']
        image=Image.frombytes('RGB',result['size'],result['pixels'])
        self._photo=ImageTk.PhotoImage(image)
        self.preview.configure(image=self._photo,text='')
        self.page_label.configure(text=f'Page {self.preview_page+1} / {self.preview_total}')
        if len(self._preview_cache)>=12 and (result['source'],result['page']) not in self._preview_cache:
            self._preview_cache.pop(next(iter(self._preview_cache)))
        self._preview_cache[(result['source'],result['page'])]=result
    def _append(self,text):
        self.log.configure(state='normal');self.log.insert('end',str(text)+'\n');self.log.see('end');self.log.configure(state='disabled')
    def _run(self):
        if self.busy:return
        op=self.operation.get();sources=tuple(self.sources);dest=self.destination.get().strip()
        kwargs=dict(profile=self.profile.get(),first=self.first.get(),last=self.last.get(),chunk=self.chunk.get(),order=self.order.get(),extraction_selection=self.extraction_selection.get(),language=self.language.get(),ocr_mode=self.ocr_mode.get(),compression_quality=self.compression_quality.get(),full_rgb_audit=self.full_rgb_audit.get(),ocr_before_office=self.ocr_before_office.get(),table_mode=self.xlsx_tables.get() if op=='xlsx' else False)
        try:
            if op in ('docx','xlsx','pptx') and self.ocr_before_office.get():
                import math
                try: angle=float(self.deskew_angle.get().strip())
                except ValueError: raise ValueError('Angle OCR : nombre entre -12 et 12')
                if not math.isfinite(angle) or not -12 <= angle <= 12:
                    raise ValueError('Angle OCR : nombre entre -12 et 12')
                if self.auto_deskew.get() and angle:
                    raise ValueError('Choisir angle manuel OU redressement automatique')
                if angle:
                    kwargs['deskew_angle_degrees']=angle
                if self.auto_deskew.get():
                    kwargs['auto_deskew']=True
            if op=='xlsx' and self.ocr_before_office.get() and self.xlsx_tables.get():
                raw=self.min_ocr_table_cells.get().strip()
                if not raw.isdecimal() or int(raw)>10000:
                    raise ValueError('Cellules OCR min/page : entier entre 0 et 10000')
                if int(raw):
                    kwargs['min_nonempty_cells_per_scanned_page']=int(raw)
            if op in ('docx','xlsx','pptx') and self.ocr_before_office.get() and any(Path(p).expanduser().is_symlink() for p in sources):
                raise ValueError('Source OCR Office : lien symbolique interdit')
            sources,dest=validate_request(op,sources,dest)
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
                self._append(f'Tâche {received_id} : {format_compression_result(payload) if kind == "success" else payload}')
                if kind=='error':messagebox.showerror('Opération impossible',explain_error(payload),parent=self)
        except queue.Empty:pass
        if self.busy and self._job_started is not None:
            self.status.configure(text=f'Traitement en cours… {int(time.monotonic()-self._job_started)} s (ne pas fermer la fenêtre)')
        self.after(100,self._poll)
if __name__=='__main__':OpenPDFStudio().mainloop()
