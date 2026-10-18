"""Validated, bounded diagnostic pipeline for explicitly supplied PDF/raster regions.

Never treats browser overlay pixels as PDF coordinates. Author: Abdelhalim Talbi.
"""
from collections import Counter
from visual_coordinate_transform import map_raster_region
from visual_text_correlation import correlate_visual_text


def prepare_spatial_diagnostic(report, limit=200):
    if not isinstance(report,dict):
        raise TypeError('report must be a dictionary')
    if type(limit) is not int or not 1<=limit<=1000:
        raise ValueError('limit must be between 1 and 1000')
    accepted=[]; rejected=Counter(); seen=set()
    raster=report.get('visual_regions_raster_space',[])
    if not isinstance(raster,list):
        rejected['invalid_raster_collection']+=1;raster=[]
    for item in raster[:limit]:
        mapped=map_raster_region(item)
        if mapped is None:
            rejected['invalid_or_unverifiable_geometry']+=1;continue
        key=(mapped['side'],mapped['page'],tuple(mapped['bbox']))
        if key in seen:
            rejected['duplicate_region']+=1;continue
        seen.add(key);accepted.append(mapped)
    if len(raster)>limit:rejected['over_limit']+=len(raster)-limit
    explicit=report.get('visual_regions_pdf_space',[])
    if not isinstance(explicit,list):
        rejected['invalid_pdf_collection']+=1;explicit=[]
    # Existing explicit rectangles are checked by correlation engine; no trust escalation.
    annotated=dict(report)
    annotated['visual_regions_pdf_space']=explicit[:limit]+accepted
    correlations=correlate_visual_text(annotated,limit=limit)
    return {'mapped_regions':accepted,'correlations':correlations,
            'rejections':dict(sorted(rejected.items())),
            'status':'candidate_spatial_overlap_only',
            'requires_human_review':True}
