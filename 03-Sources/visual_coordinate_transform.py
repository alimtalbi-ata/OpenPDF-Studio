"""Explicit raster-to-PDF rectangle mapping (unrotated, uncropped pages only).

Author: Abdelhalim Talbi. Browser masks cannot be inferred from PDF metadata.
"""
import math

def _positive(v):
    return type(v) in (int,float) and math.isfinite(v) and v>0

def map_raster_region(region):
    """Map one explicit rectangle with provenance to PDF points, or reject.

    Requires raster_width/height, pdf_width/height, bbox and rotation=0.
    Pixel coordinates refer to the complete untransformed PDF page image.
    Does not accept viewport CSS pixels, scaled overlay coordinates, crops,
    rotated pages, or screenshots with unknown provenance.
    """
    if not isinstance(region,dict):return None
    side,page=region.get('side'),region.get('page')
    if side not in ('source','target') or type(page) is not int or page<1:return None
    if region.get('coordinate_space')!='full_page_raster' or region.get('rotation',0)!=0:return None
    rw,rh,pw,ph=(region.get(k) for k in ('raster_width','raster_height','pdf_width','pdf_height'))
    if not all(_positive(x) for x in (rw,rh,pw,ph)):return None
    if max(rw,rh,pw,ph)>100000:return None
    bbox=region.get('bbox')
    if not isinstance(bbox,(list,tuple)) or len(bbox)!=4:return None
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in bbox):return None
    x0,y0,x1,y1=bbox
    if not (0<=x0<x1<=rw and 0<=y0<y1<=rh):return None
    return {'side':side,'page':page,'bbox':[round(x0*pw/rw,5),round(y0*ph/rh,5),round(x1*pw/rw,5),round(y1*ph/rh,5)],'provenance':'explicit_full_page_raster_transform','status':'candidate_pdf_coordinates'}

def convert_raster_regions(report,limit=200):
    if not isinstance(report,dict):return []
    if type(limit) is not int or not 1<=limit<=1000:raise ValueError('limit must be 1..1000')
    values=report.get('visual_regions_raster_space')
    if not isinstance(values,list):return []
    result=[]
    for item in values[:limit]:
        mapped=map_raster_region(item)
        if mapped:result.append(mapped)
    return result
