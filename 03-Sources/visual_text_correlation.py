"""Conservative correlation of explicit PDF-space visual and text rectangles.

Author: Abdelhalim Talbi. Coordinates must use the same PDF page coordinate space.
No conversion from reduced-resolution browser masks is attempted.
"""
import math


def _rect(value):
    if not isinstance(value,(list,tuple)) or len(value)!=4:return None
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in value):return None
    x0,y0,x1,y1=value
    return tuple(value) if 0<=x0<x1 and 0<=y0<y1 else None


def correlate_visual_text(report, limit=200):
    """Correlate only explicitly page-aligned PDF rectangles, never infer semantic cause."""
    if not isinstance(report,dict):return []
    regions=report.get('visual_regions_pdf_space',[])
    texts=report.get('page_annotations',[])
    if not isinstance(regions,list) or not isinstance(texts,list):return []
    out=[]
    for i,region in enumerate(regions[:limit]):
        if not isinstance(region,dict):continue
        side,page=region.get('side'),region.get('page');a=_rect(region.get('bbox'))
        if side not in ('source','target') or type(page) is not int or page<1 or not a:continue
        for j,item in enumerate(texts[:limit]):
            if not isinstance(item,dict) or item.get('side')!=side or item.get('page')!=page:continue
            b=_rect(item.get('bbox'))
            if not b:continue
            w=max(0,min(a[2],b[2])-max(a[0],b[0]));h=max(0,min(a[3],b[3])-max(a[1],b[1]));inter=w*h
            if not inter:continue
            area_a=(a[2]-a[0])*(a[3]-a[1]);area_b=(b[2]-b[0])*(b[3]-b[1]);iou=inter/(area_a+area_b-inter)
            out.append({'visual_index':i,'annotation_index':j,'side':side,'page':page,'iou':round(iou,4),'status':'spatial_overlap_only'})
            if len(out)>=limit:return out
    return out
