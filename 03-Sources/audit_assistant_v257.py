"""OpenPDF Studio V25.7 — Assistant graphique de dossiers d'audit.
Tkinter (bibliothèque standard), interface locale, sans transfert réseau.
Auteur : Abdelhalim Talbi.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from audit_dossier_v256 import create, verify, describe


def validate_create_paths(audit, source, target, output):
    """Pure validation, safe to test without a display."""
    paths = (audit, source, target, output)
    if not all(str(p).strip() for p in paths):
        raise ValueError('Sélectionnez le journal, les deux PDF et le ZIP de sortie.')
    a, s, t, o = map(lambda p: Path(p).expanduser().resolve(), paths)
    if len({a, s, t}) != 3:
        raise ValueError('Le journal, la source et la cible doivent être distincts.')
    for p in (a, s, t):
        if not p.is_file():
            raise ValueError('Fichier introuvable : ' + str(p))
    if o.suffix.lower() != '.zip':
        raise ValueError('La sortie doit être une archive .zip.')
    if o in (a, s, t):
        raise ValueError('Le ZIP ne doit pas remplacer un fichier d’entrée.')
    if not o.parent.is_dir():
        raise ValueError('Le dossier de destination est introuvable.')
    return a, s, t, o


def validate_verify_path(dossier):
    if not str(dossier).strip():
        raise ValueError('Sélectionnez un dossier ZIP à vérifier.')
    p = Path(dossier).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() != '.zip':
        raise ValueError('Archive ZIP introuvable.')
    return p


def readable_result(ok, message, manifest=None):
    """Accessible summary, independent of the GUI/display."""
    prefix = 'SUCCÈS — ' if ok else 'ÉCHEC — '
    return prefix + describe(ok, message, manifest)


class AuditAssistant(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V25.9 — Assistant d’audit')
        self.geometry('850x670')
        self.minsize(690, 560)
        self.configure(bg='#f3f6fb')
        self.fields = {k: tk.StringVar() for k in ('audit', 'source', 'target', 'output', 'dossier')}
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._busy = False
        self._build()
        self.protocol('WM_DELETE_WINDOW', self._close)

    def _build(self):
        style = ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')
        style.configure('TFrame', background='#f3f6fb')
        style.configure('TLabel', background='#f3f6fb', foreground='#243047', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#16335b')
        style.configure('TButton', padding=7, font=('Segoe UI', 10))
        root = ttk.Frame(self, padding=20); root.pack(fill='both', expand=True)
        ttk.Label(root, text='Dossiers de preuves PDF', style='Title.TLabel').pack(anchor='w')
        ttk.Label(root, text='Créer ou contrôler un dossier d’audit hors ligne — aucun envoi réseau').pack(anchor='w', pady=(3, 12))
        tabs = ttk.Notebook(root); tabs.pack(fill='both', expand=True)
        create_tab = ttk.Frame(tabs, padding=16); verify_tab = ttk.Frame(tabs, padding=16)
        tabs.add(create_tab, text='1  Constituer un dossier'); tabs.add(verify_tab, text='2  Vérifier un dossier')
        for key, label, save, types in (
            ('audit','Journal JSON SHA-256',False,[('JSON','*.json')]),
            ('source','PDF source',False,[('PDF','*.pdf')]),
            ('target','PDF cible',False,[('PDF','*.pdf')]),
            ('output','Dossier ZIP de sortie',True,[('ZIP','*.zip')]),
        ): self._field(create_tab,key,label,save,types)
        self.create_button=ttk.Button(create_tab,text='Créer et vérifier le dossier',command=self._create);self.create_button.pack(anchor='w',pady=15)
        ttk.Label(create_tab,text='Les PDF originaux sont inclus dans le ZIP : protégez ce fichier.').pack(anchor='w')
        self._field(verify_tab,'dossier','Dossier ZIP à contrôler',False,[('ZIP','*.zip')])
        self.verify_button=ttk.Button(verify_tab,text='Vérifier le dossier',command=self._verify);self.verify_button.pack(anchor='w',pady=15)
        ttk.Label(verify_tab,text='Vérification des empreintes et de la chaîne des preuves, sans signature d’identité.').pack(anchor='w')
        self.status_var=tk.StringVar(value='Prêt — sélectionnez les fichiers puis lancez le contrôle.')
        ttk.Label(root,textvariable=self.status_var).pack(anchor='w',pady=(8,0))
        self.progress=ttk.Progressbar(root,mode='indeterminate');self.progress.pack(fill='x',pady=(4,6))
        ttk.Label(root,text='Rapport de contrôle',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(12,4))
        self.report=tk.Text(root,height=9,wrap='word',font=('Consolas',10),state='disabled',bg='white',fg='#223047')
        self.report.pack(fill='both',expand=True)
        ttk.Label(root,text='Auteur : Abdelhalim Talbi  •  Contrôle d’intégrité ≠ signature numérique').pack(anchor='w',pady=(8,0))

    def _field(self,parent,key,label,save,types):
        frame=ttk.Frame(parent);frame.pack(fill='x',pady=6)
        ttk.Label(frame,text=label).pack(anchor='w')
        line=ttk.Frame(frame);line.pack(fill='x',pady=3)
        ttk.Entry(line,textvariable=self.fields[key]).pack(side='left',fill='x',expand=True)
        def browse():
            if save: path=filedialog.asksaveasfilename(parent=self,defaultextension='.zip',filetypes=types)
            else: path=filedialog.askopenfilename(parent=self,filetypes=types)
            if path:self.fields[key].set(path)
        ttk.Button(line,text='Parcourir…',command=browse).pack(side='left',padx=(8,0))

    def _display(self,ok,msg,manifest=None):
        self.report.configure(state='normal');self.report.delete('1.0','end')
        self.report.insert('1.0',readable_result(ok,msg,manifest));self.report.configure(state='disabled')
        self.status_var.set('Terminé — succès' if ok else 'Terminé — échec (voir le rapport)')

    def _start_job(self, job, success_message):
        """Run hashing/ZIP I/O off the Tk event thread; UI updates only on Tk thread."""
        if self._busy:
            return
        self._busy = True
        self.create_button.configure(state='disabled')
        self.verify_button.configure(state='disabled')
        self.progress.start(12)
        self.status_var.set('Traitement en cours — calcul SHA-256 et vérification…')
        future = self._executor.submit(job)
        def poll():
            if not self.winfo_exists():
                return
            if not future.done():
                self.after(80, poll)
                return
            self.progress.stop()
            self._busy = False
            self.create_button.configure(state='normal')
            self.verify_button.configure(state='normal')
            try:
                ok, msg, manifest = future.result()
                self._display(ok, success_message + msg if ok else msg, manifest)
            except (OSError, ValueError, TypeError, RuntimeError) as exc:
                self._display(False, str(exc))
        self.after(80, poll)

    def _create(self):
        if self._busy:
            return
        try:
            a,s,t,o=validate_create_paths(*(self.fields[k].get() for k in ('audit','source','target','output')))
            if o.exists() and not messagebox.askyesno('Remplacer le ZIP ?',f'Le fichier {o.name} existe. Le remplacer ?',parent=self):return
            def job():
                import os, tempfile
                fd,tmp=tempfile.mkstemp(prefix='.openpdf-audit-',suffix='.zip',dir=o.parent)
                os.close(fd)
                try:
                    ok,msg,manifest=create(a,s,t,tmp)
                    if not ok:raise ValueError('Vérification du dossier généré : '+msg)
                    Path(tmp).replace(o)
                    return ok,msg,manifest
                finally:
                    Path(tmp).unlink(missing_ok=True)
            self._start_job(job, 'Dossier créé et vérifié : '+str(o)+' — ')
        except (OSError,ValueError,TypeError) as exc:self._display(False,str(exc))

    def _verify(self):
        if self._busy:
            return
        try:
            p=validate_verify_path(self.fields['dossier'].get())
            self._start_job(lambda:verify(p), '')
        except (OSError,ValueError,TypeError) as exc:self._display(False,str(exc))

    def _close(self):
        if self._busy:
            if not messagebox.askyesno('Opération en cours', 'Un contrôle est en cours. Fermer la fenêtre ? Le traitement pourra se terminer en arrière-plan.', parent=self):
                return
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()

if __name__=='__main__':
    try: AuditAssistant().mainloop()
    except tk.TclError as exc: raise SystemExit('Interface graphique indisponible : '+str(exc))
