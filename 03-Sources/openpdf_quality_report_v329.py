"""Présentation lisible des contrôles de compression V32.9. Auteur : Abdelhalim Talbi."""

def quality_dashboard(report):
    """Formate un rapport de contrôles sans inventer de verdict de conformité."""
    if not isinstance(report, dict):
        raise TypeError('Rapport attendu sous forme de dictionnaire')
    gain=report.get('gain_pct')
    visual=report.get('difference_moyenne_pct')
    pages=report.get('pages_analysees', 0)
    def pct(value):
        return 'non mesuré' if value is None else f'{float(value):.2f} %'
    warnings=list(report.get('avertissements') or [])
    lines=['Bilan de compression — V32.9',f'Gain de taille : {pct(gain)}',
           f'Différence visuelle moyenne (indicative) : {pct(visual)}',
           f'Pages comparées : {int(pages)}',
           'Lisibilité et fidélité : validation humaine recommandée']
    lines += ['Avertissement : '+str(w) for w in warnings]
    return '\n'.join(lines)
