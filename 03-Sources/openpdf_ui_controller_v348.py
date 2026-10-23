"""UI-independent dispatch to stable PDF services. Author: Abdelhalim Talbi."""
from pathlib import Path
from openpdf_page_service_v345 import merge, extract, reorder, split, PageReceipt
from openpdf_compression_service_v344 import compress_with_receipt
from openpdf_ocr_service_v347 import searchable_pdf

OPERATIONS = ('compression', 'fusion', 'extraction', 'decoupage', 'reorganisation', 'ocr', 'docx', 'xlsx', 'pptx')
def run_operation(operation, sources, destination, *, profile='smaller_only', first=1, last=1, chunk=1, order='', language='fra+eng', extraction_selection=''):
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
    if operation == 'compression': return compress_with_receipt(src, destination, profile)
    if operation == 'extraction':
        # V50.0: optional non-contiguous selection shares the validated
        # reorganisation engine; legacy first/last remains the default.
        if not isinstance(extraction_selection, str):
            raise ValueError('Sélection de pages invalide')
        if extraction_selection.strip():
            import fitz
            from openpdf_page_order_v497 import parse_page_order
            with fitz.open(src) as doc:
                if doc.needs_pass or doc.page_count < 1:
                    raise ValueError('PDF source vide ou protégé')
                indices = parse_page_order(extraction_selection, doc.page_count)
            receipt = reorder(src, destination, indices)
            return PageReceipt('extract', receipt.outputs, receipt.page_counts, receipt.sha256)
        return extract(src, destination, int(first), int(last))
    if operation == 'decoupage': return split(src, destination, int(chunk))
    if operation == 'reorganisation':
        import fitz
        from openpdf_page_order_v497 import parse_page_order
        with fitz.open(src) as doc:
            if doc.needs_pass or doc.page_count < 1:
                raise ValueError('PDF source vide ou protégé')
            indices = parse_page_order(order, doc.page_count)
        return reorder(src, destination, indices)
    return searchable_pdf(src, destination, language=language)
