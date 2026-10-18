"""V33.0 — bilan de compression lisible, sans verdict automatique de conformité."""
from pathlib import Path

def build_summary(source, destination, assessment=None, visual=None):
    """Assemble des mesures factuelles, sans extrapoler un score qualité."""
    source, destination = Path(source), Path(destination)
    before, after = source.stat().st_size, destination.stat().st_size
    gain = 100*(before-after)/before if before else 0.0
    a, v = assessment or {}, visual or {}
    return {'source':str(source),'destination':str(destination),
            'before_bytes':before,'after_bytes':after,'gain_pct':round(gain,2),
            'pages_texte_modifie':a.get('pages_texte_modifie'),
            'visual':v,'warnings':(['Le fichier est plus volumineux.'] if after>before else [])}

def format_summary(data):
    from openpdf_compression_v320 import format_bytes
    if not isinstance(data,dict): raise TypeError('Dictionnaire attendu')
    gain=data['gain_pct']
    state='Réduction' if gain>0 else ('Augmentation' if gain<0 else 'Taille inchangée')
    lines=['Bilan de compression — V33.0',
           f"Original : {format_bytes(data['before_bytes'])}",
           f"Résultat : {format_bytes(data['after_bytes'])}",
           f"{state} : {abs(gain):.2f} %",
           'Qualité visuelle : indicateur seulement, contrôle humain recommandé']
    lines += ['Attention : '+str(w) for w in data.get('warnings',[])]
    return '\n'.join(lines)

def show_summary_dialog(app, data):
    """Fenêtre Tk non modale avec mesures et action de copie explicite."""
    import tkinter as tk
    from tkinter import ttk
    dialog=tk.Toplevel(app);dialog.title('Résultat de compression — V33.0');dialog.geometry('560x320')
    frame=ttk.Frame(dialog,padding=20);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Compression terminée',font=('Segoe UI',16,'bold')).pack(anchor='w',pady=(0,12))
    ttk.Label(frame,text=format_summary(data),justify='left',wraplength=500).pack(anchor='w')
    row=ttk.Frame(frame);row.pack(side='bottom',fill='x',pady=12)
    def copy():
        dialog.clipboard_clear();dialog.clipboard_append(format_summary(data))
    ttk.Button(row,text='Copier le bilan',command=copy).pack(side='left')
    ttk.Button(row,text='Fermer',command=dialog.destroy).pack(side='right')
    return dialog
