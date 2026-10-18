"""Cooperative OS-backed lock. Lockfiles remain persistent to avoid unlink races.
POSIX: flock; Windows: msvcrt.locking. Not a distributed consensus lock.
Author: Abdelhalim Talbi.
"""
from contextlib import contextmanager
from pathlib import Path
import os

class LockBusy(RuntimeError): pass

@contextmanager
def os_lock(destination):
    p=Path(destination).expanduser().resolve()
    lock=p.parent / ("."+p.name+".openpdf.oslock")
    fd=os.open(str(lock),os.O_CREAT|os.O_RDWR,0o600)
    acquired=False
    try:
        if os.name=="nt":
            import msvcrt
            os.lseek(fd,0,os.SEEK_SET)
            if os.fstat(fd).st_size==0: os.write(fd,b"\0")
            os.lseek(fd,0,os.SEEK_SET)
            try: msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            except OSError as e: raise LockBusy(str(lock)) from e
        else:
            import fcntl
            try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as e: raise LockBusy(str(lock)) from e
        acquired=True
        yield
    finally:
        if acquired:
            if os.name=="nt":
                os.lseek(fd,0,os.SEEK_SET)
                msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_UN)
        os.close(fd)
