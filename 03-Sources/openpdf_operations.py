"""Stable PDF dispatcher with cooperative cross-process output reservation.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
from time import monotonic
from openpdf_audit_v415 import write_event
from openpdf_reservation import reserve
from openpdf_split_transaction import split_transaction, recover_transactions
from openpdf_ui_controller_v348 import OPERATIONS, run_operation as _legacy_run_operation

def run_operation(operation, sources, destination, **kwargs):
    if operation not in OPERATIONS:
        raise ValueError("Opération inconnue")
    if not destination:
        raise ValueError("Destination obligatoire")
    inputs = [Path(p).expanduser().resolve() for p in sources if str(p).strip()]
    if not inputs:
        raise ValueError("Au moins une source est obligatoire")
    output = Path(destination).expanduser().resolve()
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
            else:
                result=_legacy_run_operation(operation, sources, destination, **kwargs)
            status='success'
            return result
    finally:
        write_event(operation,status,round((monotonic()-started)*1000))

__all__ = ["OPERATIONS", "run_operation"]


def recover_split(destination):
    """Explicit recovery, serialized with all cooperating split jobs."""
    output=Path(destination).expanduser().resolve()
    with reserve(output / ".openpdf-split"):
        return recover_transactions(output)
