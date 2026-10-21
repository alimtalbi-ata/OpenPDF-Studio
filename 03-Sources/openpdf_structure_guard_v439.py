"""PDF structure preservation gate, V43.9. Author: Abdelhalim Talbi.

Compares interactive PDF content before publication. Raster equality alone cannot
prove link, annotation, form, outline or attachment preservation. This is not
PDF/A or cryptographic signature verification.
"""
import hashlib
import fitz

def _value(obj):
    if isinstance(obj, (fitz.Point, fitz.Rect, fitz.IRect)):
        return tuple(round(float(x), 3) for x in obj)
    if isinstance(obj, float):
        return round(obj, 3)
    if isinstance(obj, (list, tuple)):
        return tuple(_value(x) for x in obj)
    if isinstance(obj, dict):
        return tuple(sorted((str(k), _value(v)) for k, v in obj.items()))
    if obj is None or isinstance(obj, (str, int, bool)):
        return obj
    raise RuntimeError('Structure PDF non prise en charge')

def _page(page):
    links = []
    for link in page.get_links():
        links.append(_value({k: v for k, v in link.items() if k not in ('xref', 'id')}))
    annots = []
    for annot in page.annots() or ():
        info = {k: v for k, v in annot.info.items() if k not in ('id', 'modDate', 'creationDate')}
        annots.append(_value((annot.type[0], annot.rect, annot.flags, info,
                             annot.colors, annot.opacity)))
    widgets = []
    for widget in page.widgets() or ():
        if widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE:
            raise RuntimeError('Champ de signature : compression refusée')
        fields = ('field_name', 'field_type', 'field_value', 'field_flags',
                  'rect', 'field_label', 'choice_values')
        widgets.append(_value({key: getattr(widget, key, None) for key in fields}))
    return tuple(tuple(sorted(x, key=repr)) for x in (links, annots, widgets))

def _snapshot(doc):
    if doc.needs_pass:
        raise RuntimeError('PDF protégé : vérification impossible')
    metadata = doc.metadata or {}
    descriptive = {k: metadata.get(k, '') for k in ('title', 'author', 'subject', 'keywords')}
    outline = []
    for level, title, page, target in doc.get_toc(simple=False):
        outline.append((level, title, page, _value({k: v for k, v in target.items() if k != 'xref'})))
    files = tuple((name, hashlib.sha256(doc.embfile_get(name)).hexdigest())
                  for name in sorted(doc.embfile_names()))
    return (_value(descriptive), _value(doc.get_page_labels()),
            tuple(outline), files, tuple(_page(p) for p in doc))

def validate_structure_preserved(source, candidate):
    """Reject a temporary PDF candidate with changed interactive structures."""
    with fitz.open(str(source)) as original, fitz.open(str(candidate)) as output:
        if not original.page_count or original.page_count != output.page_count:
            raise RuntimeError('Nombre de pages PDF modifié : sortie rejetée')
        before, after = _snapshot(original), _snapshot(output)
        categories = ('Métadonnées', 'Étiquettes de pages', 'Signets',
                      'Pièces jointes', 'Liens/annotations/formulaires')
        for name, left, right in zip(categories, before, after):
            if left != right:
                raise RuntimeError(f'{name} PDF modifiés : sortie rejetée')
        return {'pages_verified': original.page_count,
                'links_verified': sum(len(p[0]) for p in before[4]),
                'annotations_verified': sum(len(p[1]) for p in before[4]),
                'widgets_verified': sum(len(p[2]) for p in before[4]),
                'attachments_verified': len(before[3]),
                'bookmarks_verified': len(before[2])}
