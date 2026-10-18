"""Non-mutating cooperative lock inspection; no automatic lock reclamation."""
from pathlib import Path
import os,socket
from openpdf_reservation import lock_path,read_owner

def inspect_lock(destination):
    lock=lock_path(destination)
    owner=read_owner(destination)
    state=owner["status"]
    if state=="absent":return {"status":"absent","lock":str(lock)}
    if state not in ("metadata_valid","legacy_pid_only"):
        return {"status":"unknown","lock":str(lock),"action":"manual_review"}
    pid=owner["pid"]
    report={"status":"unverified","pid":pid,"lock":str(lock),"action":"manual_review","owner_format":state}
    if state=="metadata_valid":
        report["hostname"]=owner.get("hostname")
        report["created_at"]=owner.get("created_at")
        report["token_present"]=True
        if owner.get("hostname")!=socket.gethostname():
            report["status"]="remote_host_unverified"
            return report
    if os.name!="posix":return report
    try:os.kill(pid,0)
    except ProcessLookupError:report["status"]="possibly_orphaned"
    except PermissionError:report["status"]="active_or_inaccessible"
    else:report["status"]="pid_exists_unverified"
    return report
