"""Cooperative exclusive locks with verified owner token and backwards compatibility.
No automatic stale lock stealing. Author: Abdelhalim Talbi.
"""
from contextlib import contextmanager
from openpdf_os_lock import os_lock, LockBusy
from pathlib import Path
import os, json, secrets, socket, time


def lock_path(path):
    p=Path(path).expanduser().resolve()
    return p.parent / ("."+p.name+".openpdf.lock")


def read_owner(path):
    return read_owner_from_lock(lock_path(path))

def read_owner_from_lock(lock):
    try:
        raw=lock.read_text(encoding="utf-8").strip()
        try:
            obj=json.loads(raw)
            if isinstance(obj,int) and obj>0: return {"status":"legacy_pid_only","pid":obj}
            if isinstance(obj,dict) and obj.get("schema")==2 and isinstance(obj.get("pid"),int) and obj["pid"]>0 and isinstance(obj.get("token"),str) and len(obj["token"])>=32:
                return {"status":"metadata_valid",**obj}
        except (ValueError,TypeError):
            if raw.isdecimal() and int(raw)>0:
                return {"status":"legacy_pid_only","pid":int(raw)}
        return {"status":"invalid"}
    except FileNotFoundError: return {"status":"absent"}
    except (OSError,UnicodeError): return {"status":"unreadable"}


@contextmanager
def reserve(path):
    lock=lock_path(path)
    token=secrets.token_hex(24)
    payload={"schema":2,"pid":os.getpid(),"token":token,"hostname":socket.gethostname(),"created_at":time.time()}
    manager=os_lock(path)
    try:
        manager.__enter__()
    except LockBusy as exc:
        raise FileExistsError(str(lock)) from exc
    try:
        with _reserve_legacy(lock, token, payload):
            yield
    finally:
        manager.__exit__(None,None,None)

@contextmanager
def _reserve_legacy(lock, token, payload):
    fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    owned_stat=os.fstat(fd)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(payload,f,sort_keys=True);f.write("\n");f.flush();os.fsync(f.fileno())
        yield
    finally:
        # Do not delete a lock replaced by another writer; inode and token must match.
        try:
            current=read_owner_from_lock(lock)
            if current.get("token")==token:
                # Identity check rejects replacement even when metadata is copied.
                observed=os.lstat(lock)
                if (observed.st_dev,observed.st_ino)==(owned_stat.st_dev,owned_stat.st_ino):
                    lock.unlink()
        except OSError:
            pass


def inspect_orphan(destination):
    """Conservative diagnosis; never deletes. Same-host PID absence is only a hint."""
    owner=read_owner(destination)
    if owner.get("status")!="metadata_valid":
        return {"status":owner.get("status"),"recoverable":False}
    if owner.get("hostname")!=socket.gethostname():
        return {"status":"remote_host","recoverable":False}
    pid=owner["pid"]
    try:
        os.kill(pid,0)
    except ProcessLookupError:
        return {"status":"pid_absent","recoverable":True}
    except (PermissionError,OSError):
        return {"status":"pid_unverifiable","recoverable":False}
    return {"status":"pid_present","recoverable":False}

def recover_orphan(destination, *, confirm=False):
    """Explicit recovery only; serializes cooperative peers using OS lock.
    Rejects legacy locks, remote hosts, live/unverifiable PIDs.
    """
    if not confirm: raise PermissionError("explicit confirmation required")
    lock=lock_path(destination)
    with os_lock(destination):
        state=inspect_orphan(destination)
        if state["status"]!="pid_absent":
            raise PermissionError("cannot safely recover: "+state["status"])
        before=os.lstat(lock)
        owner=read_owner_from_lock(lock)
        expected_token=owner.get("token")
        if owner.get("status")!="metadata_valid": raise PermissionError("lock changed")
        # Re-check immediately before unlink. OS lock prevents cooperating writers.
        if inspect_orphan(destination)["status"]!="pid_absent": raise PermissionError("owner status changed")
        after=os.lstat(lock)
        current=read_owner_from_lock(lock)
        if current.get("token")!=expected_token or current.get("status")!="metadata_valid":
            raise PermissionError("owner token changed")
        if (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino):
            raise PermissionError("lock replaced")
        lock.unlink()
        return {"status":"recovered","lock":str(lock)}
