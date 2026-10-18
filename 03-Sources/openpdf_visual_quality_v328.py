"""Contrôle visuel échantillonné, indicatif, sans OCR. Auteur : Abdelhalim Talbi."""
from pathlib import Path

def sample_pages(count, limit=5):
    """Échantillon déterministe couvrant début, milieu et fin."""
    if count < 1 or limit < 1: raise ValueError('Échantillonnage invalide')
    return sorted({round(i*(count-1)/(min(count,limit)-1)) for i in range(min(count,limit))}) if count>1 else [0]

def visual_report(source,candidate,*,max_pages=5,dpi=72):
    """Différence moyenne de luminance des pixels sur des pages rendues.

    Score informatif : 0 signifie rendu identique à ce DPI ; ce n'est pas un
    score perceptuel ni une garantie de lisibilité ou de conformité PDF.
    """
    import fitz
    if not 36 <= dpi <= 144:raise ValueError('DPI hors limites')
    with fitz.open(str(source)) as original,fitz.open(str(candidate)) as result:
        if original.needs_pass or result.needs_pass:raise ValueError('PDF protégé')
        if len(original)!=len(result) or len(original)==0:raise ValueError('Nombre de pages incohérent')
        total=len(original)
        indices=sample_pages(total,max_pages)
        samples=[]
        for i in indices:
            a=original[i].get_pixmap(dpi=dpi,colorspace=fitz.csGRAY,alpha=False)
            b=result[i].get_pixmap(dpi=dpi,colorspace=fitz.csGRAY,alpha=False)
            if a.width!=b.width or a.height!=b.height:
                samples.append({'page':i+1,'difference_pct':None,'reason':'Dimensions rendues différentes'})
                continue
            x,y=a.samples,b.samples
            difference=sum(abs(u-v) for u,v in zip(x,y))/(255*len(x))*100 if x else 0
            samples.append({'page':i+1,'difference_pct':round(difference,3)})
    values=[p['difference_pct'] for p in samples if p['difference_pct'] is not None]
    return {'pages_analysees':len(samples),'pages_total':total,
            'echantillon':samples,'difference_moyenne_pct':round(sum(values)/len(values),3) if values else None,
            'limites':'Mesure de pixels échantillonnés à faible résolution ; ne garantit pas la lisibilité ni la conservation des métadonnées.'}

def visual_summary(report):
    avg=report['difference_moyenne_pct']
    detail='non comparable' if avg is None else f'{avg:.3f} %'
    return f"Contrôle visuel indicatif : {report['pages_analysees']} page(s) échantillonnée(s), différence moyenne {detail}. {report['limites']}"
