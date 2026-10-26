"""Stable PDF dispatcher with cooperative cross-process output reservation.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
from time import monotonic
from openpdf_audit_v415 import write_event
from openpdf_reservation import reserve
from openpdf_split_transaction import split_transaction, recover_transactions
from openpdf_ui_controller_v348 import OPERATIONS, run_operation as _legacy_run_operation
from openpdf_source_path_guard_v548 import guard_pdf_source_path
from openpdf_destination_path_guard_v549 import guard_destination_path

def run_operation(operation, sources, destination, **kwargs):
    if operation not in OPERATIONS:
        raise ValueError("Opération inconnue")
    table_mode = kwargs.get('table_mode', False)
    minimum_cells = kwargs.get('min_nonempty_cells_per_scanned_page', 0)
    deskew_angle = kwargs.get('deskew_angle_degrees', 0.0)
    auto_deskew = kwargs.get('auto_deskew', False)
    import math
    if (type(deskew_angle) not in (int, float) or not math.isfinite(deskew_angle)
            or not -12 <= deskew_angle <= 12
            or (deskew_angle and not (operation in ('docx', 'xlsx', 'pptx')
                                      and kwargs.get('ocr_before_office', False)))):
        raise ValueError('Angle de redressement OCR invalide ou OCR Office non active')
    if (type(auto_deskew) is not bool or
            (auto_deskew and (deskew_angle or operation not in ('docx', 'xlsx', 'pptx')
                              or not kwargs.get('ocr_before_office', False)))):
        raise ValueError('Redressement OCR automatique invalide ou incompatible')
    if (type(minimum_cells) is not int or not 0 <= minimum_cells <= 10000
            or (minimum_cells and not (operation == 'xlsx' and table_mode
                                       and kwargs.get('ocr_before_office', False)))):
        raise ValueError('Seuil de cellules OCR invalide ou OCR Excel non active')
    if type(table_mode) is not bool or (table_mode and operation != 'xlsx'):
        raise ValueError('Mode tableaux réservé à la conversion Excel')
    if not destination:
        raise ValueError("Destination obligatoire")
    # Reject linked destination ancestors before canonicalization or reservation.
    output = guard_destination_path(
        destination, directory=(operation == "decoupage"), allow_existing=True
    )
    # Validate every lexical source component before the operation starts.
    source_paths = [guard_pdf_source_path(p) for p in sources if str(p).strip()]
    inputs = source_paths
    if not inputs:
        raise ValueError("Au moins une source est obligatoire")
    if operation == "decoupage":
        if not output.is_dir():
            raise ValueError("Le découpage exige un dossier existant")
        # Serializes cooperating split jobs sharing a destination folder.
        reservation = output / ".openpdf-split"
    else:
        if output in inputs:
            raise ValueError("Refus d'écraser une source")
        if not output.parent.is_dir():
            raise ValueError("Dossier de destination inexistant")
        reservation = output
    started=monotonic()
    status='failure'
    try:
        with reserve(reservation):
            if operation != "decoupage" and output.exists():
                raise FileExistsError(f"Destination existante : {output}")
            if operation == "decoupage":
                if len(inputs) != 1:
                    raise ValueError("Le découpage exige une seule source")
                result=split_transaction(inputs[0], output, int(kwargs.get("chunk", 1)))
            elif operation == "compression" and kwargs.get("profile") == "auto_quality":
                if len(inputs) != 1:
                    raise ValueError("La compression automatique exige un seul PDF source")
                from openpdf_auto_compression_v505 import auto_compress_gui
                result = auto_compress_gui(str(inputs[0]), str(output))
            elif operation in ("docx", "xlsx", "pptx") and kwargs.get("ocr_before_office", False):
                # OCR is explicitly selected; for XLSX the independent table
                # opt-in is passed through to the verified OCR Office pipeline.
                if len(inputs) != 1:
                    raise ValueError("La conversion Office exige un seul PDF source")
                from openpdf_ocr_office_pipeline_v511 import convert_scanned_office
                table_options = {'table_mode': table_mode} if operation == 'xlsx' else {}
                if minimum_cells:
                    table_options['min_nonempty_cells_per_scanned_page'] = minimum_cells
                if deskew_angle:
                    table_options['deskew_angle_degrees'] = float(deskew_angle)
                if auto_deskew:
                    table_options['auto_deskew'] = True
                result=convert_scanned_office(inputs[0], output,
                                              language=kwargs.get("language", "fra+eng"),
                                              **table_options)
            elif operation == 'xlsx' and table_mode:
                if len(inputs) != 1:
                    raise ValueError('La conversion Excel exige un seul PDF source')
                from openpdf_conversion_service_v351 import convert_office
                result = convert_office(inputs[0], output, output_format='xlsx', table_mode=True)
            else:
                result=_legacy_run_operation(operation, inputs, destination, **kwargs)
            # Compression 'smaller_only' can legitimately yield no new output.
            # Audit must distinguish that outcome from a published document.
            if operation == 'compression' and (
                    getattr(result, 'published', True) is False
                    or (isinstance(result, str) and result.startswith(
                        'Aucun gain conforme aux seuils de qualité.'))):
                status='no_output'
            else:
                status='success'
            return result
    finally:
        write_event(operation,status,round((monotonic()-started)*1000))

__all__ = ["OPERATIONS", "run_operation"]


def recover_split(destination):
    """Explicit recovery, serialized with all cooperating split jobs."""
    output=guard_destination_path(destination, directory=True)
    with reserve(output / ".openpdf-split"):
        return recover_transactions(output)
