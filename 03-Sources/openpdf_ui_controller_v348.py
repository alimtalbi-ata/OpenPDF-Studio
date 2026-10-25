"""UI-independent dispatch to stable PDF services. Author: Abdelhalim Talbi."""
from pathlib import Path
from openpdf_page_service_v345 import merge, extract, reorder, split
from openpdf_compression_service_v344 import compress_with_receipt
from openpdf_ocr_service_v347 import searchable_pdf
from openpdf_rotation_v446 import rotate_pdf

OPERATIONS = ('compression', 'fusion', 'extraction', 'decoupage', 'reorganisation', 'rotation', 'ocr', 'docx', 'xlsx', 'pptx')
def run_operation(operation, sources, destination, *, profile='smaller_only', first=1, last=1, chunk=1, order='', language='fra+eng'):
    if operation not in OPERATIONS: raise ValueError('Opération inconnue')
    paths = [str(Path(p)) for p in sources if str(p).strip()]
    if not paths: raise ValueError('Sélectionnez au moins un fichier PDF')
    if not destination: raise ValueError('Destination obligatoire')
    if operation == 'fusion': return merge(paths, destination)
    if operation in ('docx', 'xlsx', 'pptx'):
        from openpdf_conversion_service_v351 import convert_office
        if len(paths) != 1: raise ValueError('Conversion : un seul PDF source requis')
        return convert_office(paths[0], destination, output_format=operation)
    if len(paths) != 1: raise ValueError('Cette opération nécessite exactement un fichier source')
    src = paths[0]
    if operation == 'rotation': return rotate_pdf(src,destination,int(order))
    if operation == 'compression': return compress_with_receipt(src, destination, profile)
    if operation == 'extraction': return extract(src, destination, int(first), int(last))
    if operation == 'decoupage': return split(src, destination, int(chunk))
    if operation == 'reorganisation': return reorder(src, destination, [int(x.strip()) for x in order.split(',') if x.strip()])
    return searchable_pdf(src, destination, language=language)
