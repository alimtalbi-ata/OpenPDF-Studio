"""UI-independent dispatch to stable PDF services. Author: Abdelhalim Talbi."""
from pathlib import Path
from openpdf_page_service_v345 import merge, extract, reorder, split, PageReceipt
from openpdf_compression_service_v344 import CompressionRequest, execute_compression
from openpdf_compression_ui_v471 import resolve_quality_mode
from openpdf_ocr_service_v347 import searchable_pdf

OCR_MODES = {'Pages sans texte': True, 'Pages mixtes (intelligent)': 'smart', 'Toutes les pages': False}

OPERATIONS = ('compression', 'fusion', 'extraction', 'decoupage', 'reorganisation', 'ocr', 'docx', 'xlsx', 'pptx')
def run_operation(operation, sources, destination, *, profile='smaller_only', first=1, last=1, chunk=1, order='', language='fra+eng', ocr_mode='Pages sans texte', compression_quality='Sans audit (rapide)', full_rgb_audit=False, extraction_selection=''):
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
    if operation == 'compression':
        if type(full_rgb_audit) is not bool:
            raise ValueError('Option de contrôle RGB invalide')
        measure, gate = resolve_quality_mode(compression_quality)
        # V49.0: the full-pixel acceptance gate is independent from legacy
        # sampled presets. It is opt-in because rendering every pixel costs CPU.
        full_gate = None
        if full_rgb_audit:
            from openpdf_compression_acceptance_v489 import AcceptancePolicy
            full_gate = AcceptancePolicy(min_saving_percent=0, max_page_mae=4,
                                         max_page_changed_fraction=0.02,
                                         render_scale=0.5, pixel_delta=24)
        return execute_compression(CompressionRequest(src, destination, profile,
                                                      measure_visual=measure, quality_gate=gate,
                                                      full_pixel_gate=full_gate))
    if operation == 'extraction':
        # V50.0: optional non-contiguous extraction uses the same bounded
        # selection grammar and fidelity-checked PDF writer as reorganisation.
        # Legacy first/last extraction is unchanged when the field is blank.
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
        # Validate the complete expression and the PDF bounds before writing.
        with fitz.open(src) as doc:
            if doc.needs_pass or doc.page_count < 1:
                raise ValueError('PDF source vide ou protégé')
            indices = parse_page_order(order, doc.page_count)
        return reorder(src, destination, indices)
    if ocr_mode not in OCR_MODES:
        raise ValueError('Mode OCR inconnu')
    return searchable_pdf(src, destination, language=language, skip_text=OCR_MODES[ocr_mode])
