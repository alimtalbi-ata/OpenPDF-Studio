"""Conservative diagnostic trust assessment; not a conversion accuracy score.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

def assess_report_quality(report: dict, findings: list[dict]) -> dict:
    if not isinstance(report, dict) or not isinstance(findings, list):
        raise ValueError("Expected report object and findings list")
    limitations=[]
    source=report.get('source') or {}
    target=report.get('target') or {}
    if not isinstance(source,dict):source={}
    if not isinstance(target,dict):target={}
    if report.get('layout_comparable') is not True:
        limitations.append('Comparaison géométrique non certifiée : deux rendus PDF comparables non confirmés.')
    if not report.get('multipage_audit'):
        limitations.append('Audit de pagination absent ou vide.')
    if not report.get('pdf_office_table_audit'):
        limitations.append('Audit de tableaux PDF/Office absent ou vide.')
    if not report.get('page_annotations'):
        limitations.append('Aucune annotation géométrique explicite : les zones ne peuvent pas être surlignées automatiquement.')
    if any(x.get('severity')=='high' for x in findings if isinstance(x,dict)):
        limitations.append('Anomalies de gravité élevée : validation humaine requise.')
    for side,item in (('source',source),('cible',target)):
        geometry=item.get('geometry')
        if geometry not in ('native_pdf','libreoffice_rendered_pdf'):
            limitations.append(f'Géométrie du document {side} non attestée par un rendu PDF.')
    if not limitations:
        label='Couverture documentée'
        explanation='Les principales preuves techniques sont présentes ; la fidélité n’est pas certifiée.'
    else:
        label='Couverture partielle'
        explanation=f'{len(limitations)} limite(s) de qualification identifiée(s). Aucun score de fidélité artificiel.'
    return {'label':label,'explanation':explanation,'limitations':limitations,'fully_verified':False}
