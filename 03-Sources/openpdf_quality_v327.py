"""V32.7 — estimation prudente et contrôle qualité des sorties PDF. Auteur : Abdelhalim Talbi."""
from pathlib import Path

def assess_candidate(source, candidate):
    """Inspecte la sortie réelle ; ne prétend pas prédire le gain."""
    import fitz
    a,b=Path(source),Path(candidate)
    if not a.is_file() or not b.is_file():raise FileNotFoundError('Source ou candidat absent')
    before,after=a.stat().st_size,b.stat().st_size
    with fitz.open(a) as original,fitz.open(b) as output:
        if original.needs_pass or output.needs_pass:raise ValueError('PDF protégé')
        if len(original)!=len(output):raise ValueError('Nombre de pages modifié')
        if not len(original):raise ValueError('PDF vide')
        pages=len(original)
        text_changes=[]
        for i,(page_a,page_b) in enumerate(zip(original,output)):
            if page_a.get_text('text')!=page_b.get_text('text'):text_changes.append(i+1)
    return {'avant_octets':before,'apres_octets':after,'gain_octets':before-after,
            'gain_pourcent':round(100*(before-after)/before,2) if before else 0,
            'pages':pages,'pages_texte_modifie':text_changes,
            'taille_reduite':after<before}

def quality_summary(report):
    state=('Réduction' if report['taille_reduite'] else 'Aucun gain de taille')
    return (f"{state} : {report['gain_pourcent']:+.2f} % "
            f"({report['avant_octets']} → {report['apres_octets']} octets). "
            f"Pages : {report['pages']}. "
            f"Texte extrait modifié : {len(report['pages_texte_modifie'])} page(s). "
            'Attention : le contrôle du texte ne garantit pas la fidélité visuelle des images.')
