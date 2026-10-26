"""Windows handle-relative, fail-closed publication for OpenPDF Studio V551.

This implementation uses NT native handle-relative opens and FileLinkInformation.
It is intentionally restricted to local drive-letter paths and filesystems that
support exclusive hard-link creation. Unsupported cases fail closed.
Author: Abdelhalim Talbi.
"""
import ctypes
import os
from ctypes import wintypes
from pathlib import Path
import unicodedata

# Win32 access/share/attribute flags.
_FILE_LIST_DIRECTORY = 0x0001
_FILE_READ_DATA = 0x0001
_FILE_WRITE_DATA = 0x0002
_FILE_READ_ATTRIBUTES = 0x0080
_FILE_WRITE_ATTRIBUTES = 0x0100
_FILE_ADD_FILE = 0x0002
_DELETE = 0x00010000
_SYNCHRONIZE = 0x00100000
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_FILE_OPEN = 1
_FILE_DIRECTORY_FILE = 0x00000001
_FILE_NON_DIRECTORY_FILE = 0x00000040
_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
_FILE_OPEN_REPARSE_POINT = 0x00200000
_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_OPEN_EXISTING = 3
_OBJ_CASE_INSENSITIVE = 0x00000040
_OBJ_DONT_REPARSE = 0x00001000
_FILE_LINK_INFORMATION_CLASS = 11
_STATUS_OBJECT_NAME_COLLISION = 0xC0000035
_STATUS_OBJECT_NAME_EXISTS = 0x40000000
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", _FILETIME),
        ("ftLastAccessTime", _FILETIME),
        ("ftLastWriteTime", _FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


class _UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class _OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(_UNICODE_STRING)),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", wintypes.LPVOID),
        ("SecurityQualityOfService", wintypes.LPVOID),
    ]


class _IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [("Status", wintypes.LONG), ("Information", ctypes.c_size_t)]


class _FILE_LINK_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("ReplaceIfExists", ctypes.c_ubyte),
        ("RootDirectory", wintypes.HANDLE),
        ("FileNameLength", wintypes.ULONG),
        ("FileName", wintypes.WCHAR * 1),
    ]


def supports_windows_native_publication():
    """Return whether this process can load the native Windows primitives."""
    return os.name == "nt" and hasattr(ctypes, "WinDLL")


def _apis():
    if not supports_windows_native_publication():
        raise OSError("Publication Windows par handles indisponible hors Windows")
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll")
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
            wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
        ]
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.GetFileInformationByHandle.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION),
        ]
        kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
        kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
        kernel32.FlushFileBuffers.restype = wintypes.BOOL
        kernel32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetDriveTypeW.restype = wintypes.UINT
        ntdll.NtCreateFile.argtypes = [
            ctypes.POINTER(wintypes.HANDLE), wintypes.ULONG,
            ctypes.POINTER(_OBJECT_ATTRIBUTES), ctypes.POINTER(_IO_STATUS_BLOCK),
            ctypes.POINTER(ctypes.c_longlong), wintypes.ULONG, wintypes.ULONG,
            wintypes.ULONG, wintypes.ULONG, wintypes.LPVOID, wintypes.ULONG,
        ]
        ntdll.NtCreateFile.restype = wintypes.LONG
        ntdll.NtSetInformationFile.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_IO_STATUS_BLOCK), wintypes.LPVOID,
            wintypes.ULONG, wintypes.INT,
        ]
        ntdll.NtSetInformationFile.restype = wintypes.LONG
        ntdll.RtlNtStatusToDosError.argtypes = [wintypes.LONG]
        ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG
        return kernel32, ntdll
    except (AttributeError, OSError) as exc:
        raise OSError("API native de publication Windows indisponible; publication refusée") from exc


def _close(kernel32, handle):
    if handle not in (None, 0, _INVALID_HANDLE_VALUE):
        kernel32.CloseHandle(wintypes.HANDLE(handle))


def _win32_error(context):
    code = ctypes.get_last_error()
    raise OSError(code, context)


def _nt_error(ntdll, status, context):
    unsigned_status = int(status) & 0xFFFFFFFF
    if unsigned_status in (_STATUS_OBJECT_NAME_COLLISION, _STATUS_OBJECT_NAME_EXISTS):
        raise FileExistsError(17, "Destination existante; aucune donnée remplacée")
    code = int(ntdll.RtlNtStatusToDosError(wintypes.LONG(status)))
    if code == 0:
        code = 1
    raise OSError(code, context + " (NTSTATUS 0x%08X)" % unsigned_status)


def _info(kernel32, handle):
    result = _BY_HANDLE_FILE_INFORMATION()
    if not kernel32.GetFileInformationByHandle(wintypes.HANDLE(handle), ctypes.byref(result)):
        _win32_error("Impossible de lire l'identité du handle")
    return result


def _identity(info):
    return (
        int(info.dwVolumeSerialNumber),
        (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow),
    )


def _is_reparse(info):
    return bool(int(info.dwFileAttributes) & _FILE_ATTRIBUTE_REPARSE_POINT)


def _is_directory(info):
    return bool(int(info.dwFileAttributes) & _FILE_ATTRIBUTE_DIRECTORY)


def _check_component(name):
    if not isinstance(name, str) or not name or name in (".", ".."):
        raise ValueError("Composant de chemin Windows invalide")
    if any(char in name for char in ("\\", "/", ":", "\x00")):
        raise ValueError("Composant de chemin Windows ambigu")
    if name.endswith((".", " ")):
        raise ValueError("Nom Windows terminé par un point ou une espace refusé")
    if len(name.encode("utf-16-le")) > 510:
        raise ValueError("Composant Windows trop long")
    stem = name.split(".", 1)[0].rstrip(" .").upper()
    if stem in {"CON", "PRN", "AUX", "NUL"} or (
        len(stem) == 4 and stem[:3] in {"COM", "LPT"} and stem[3] in "123456789"
    ):
        raise ValueError("Nom de périphérique Windows réservé")
    return name


def _open_relative(kernel32, ntdll, parent, name, desired_access, share_access, options):
    name = _check_component(name)
    encoded = name.encode("utf-16-le")
    if len(encoded) > 0xFFFE:
        raise ValueError("Nom natif Windows trop long")
    name_buffer = ctypes.create_unicode_buffer(name)
    unicode_name = _UNICODE_STRING(
        len(encoded), len(encoded) + 2, ctypes.cast(name_buffer, wintypes.LPWSTR)
    )
    object_attributes = _OBJECT_ATTRIBUTES(
        ctypes.sizeof(_OBJECT_ATTRIBUTES), wintypes.HANDLE(parent),
        ctypes.pointer(unicode_name), _OBJ_CASE_INSENSITIVE | _OBJ_DONT_REPARSE,
        None, None,
    )
    io_status = _IO_STATUS_BLOCK()
    result_handle = wintypes.HANDLE()
    status = ntdll.NtCreateFile(
        ctypes.byref(result_handle), desired_access, ctypes.byref(object_attributes),
        ctypes.byref(io_status), None, 0, share_access, _FILE_OPEN, options,
        None, 0,
    )
    if int(status) < 0:
        _nt_error(ntdll, status, "Ouverture relative sans suivi de reparse point refusée")
    if not result_handle.value:
        raise OSError("NtCreateFile n'a pas retourné de handle valide")
    return result_handle.value


def _open_root(kernel32, anchor, require_add_file=False):
    # DRIVE_REMOTE=4: reject mapped network drives, even if they have a letter.
    if int(kernel32.GetDriveTypeW(anchor)) == 4:
        raise OSError("Publication V551 refuse un lecteur réseau")
    handle = kernel32.CreateFileW(
        anchor,
        _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE | (_FILE_ADD_FILE if require_add_file else 0),
        _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
        None, _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle in (None, _INVALID_HANDLE_VALUE):
        _win32_error("Ouverture du volume de destination impossible")
    info = _info(kernel32, handle)
    if not _is_directory(info) or _is_reparse(info):
        _close(kernel32, handle)
        raise OSError("La racine Windows n'est pas un répertoire ordinaire")
    return handle


def _absolute_local_drive_path(path):
    path = Path(path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    anchor = path.anchor
    if (
        len(anchor) != 3 or anchor[1:] != ":\\"
        or anchor[0].upper() not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        or str(path).startswith("\\\\")
    ):
        raise OSError("Publication native V551 limitée aux chemins absolus sur lecteur local")
    if any(component == ".." for component in path.parts[1:]):
        raise ValueError("Les segments '..' sont refusés par la publication native")
    return path


def _open_directory_chain(kernel32, ntdll, directory, require_add_file=False):
    path = _absolute_local_drive_path(directory)
    components = [part for part in path.parts[1:] if part not in ("", ".")]
    current = _open_root(kernel32, path.anchor, require_add_file=require_add_file and not components)
    access = _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE
    share = _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE
    options = _FILE_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT
    try:
        for index, component in enumerate(components):
            child_access = access | (_FILE_ADD_FILE if require_add_file and index == len(components) - 1 else 0)
            child = _open_relative(kernel32, ntdll, current, component, child_access, share, options)
            try:
                info = _info(kernel32, child)
                if not _is_directory(info) or _is_reparse(info):
                    raise OSError("Composant parent lié, reparse ou non répertoire")
            except BaseException:
                _close(kernel32, child)
                raise
            _close(kernel32, current)
            current = child
        return current
    except BaseException:
        _close(kernel32, current)
        raise


def _create_exclusive_link(ntdll, source_handle, destination_parent_handle, leaf):
    leaf = _check_component(leaf)
    encoded = leaf.encode("utf-16-le")
    size = _FILE_LINK_INFORMATION.FileName.offset + len(encoded)
    buffer = ctypes.create_string_buffer(size)
    info = ctypes.cast(buffer, ctypes.POINTER(_FILE_LINK_INFORMATION))
    info.contents.ReplaceIfExists = 0
    info.contents.RootDirectory = wintypes.HANDLE(destination_parent_handle)
    info.contents.FileNameLength = len(encoded)
    ctypes.memmove(
        ctypes.addressof(buffer) + _FILE_LINK_INFORMATION.FileName.offset,
        encoded, len(encoded),
    )
    io_status = _IO_STATUS_BLOCK()
    status = ntdll.NtSetInformationFile(
        wintypes.HANDLE(source_handle), ctypes.byref(io_status),
        ctypes.cast(buffer, wintypes.LPVOID), size, _FILE_LINK_INFORMATION_CLASS,
    )
    if int(status) < 0:
        _nt_error(ntdll, status, "Création du lien dur exclusif par handle refusée")


def _verify_path_still_uses_directory(kernel32, ntdll, path, pinned_handle):
    reopened = None
    try:
        reopened = _open_directory_chain(kernel32, ntdll, path)
        if _identity(_info(kernel32, reopened)) != _identity(_info(kernel32, pinned_handle)):
            raise RuntimeError("Dossier de publication déplacé ou remplacé; revue manuelle requise")
    except (OSError, ValueError, RuntimeError) as exc:
        if isinstance(exc, RuntimeError) and "déplacé ou remplacé" in str(exc):
            raise
        raise RuntimeError(
            "Dossier de publication déplacé ou remplacé; revue manuelle requise"
        ) from exc
    finally:
        if reopened is not None:
            _close(kernel32, reopened)


def publish_exclusive_windows(temporary, destination):
    """Create an exclusive hard link via pinned Windows directory/file handles.

    A parent is traversed component by component with NtCreateFile using
    OBJ_DONT_REPARSE and FILE_OPEN_REPARSE_POINT. The temporary file is opened
    without delete sharing, flushed, and linked by handle with ReplaceIfExists
    false. Unsupported APIs, non-local paths, non-hardlink filesystems, and
    ambiguous path changes fail closed. The temporary name is preserved.
    """
    kernel32, ntdll = _apis()
    temporary = _absolute_local_drive_path(temporary)
    destination = _absolute_local_drive_path(destination)
    original_destination = Path(destination)
    if not temporary.name or not destination.name:
        raise ValueError("Chemin de publication invalide")
    if unicodedata.normalize("NFKC", temporary.name).casefold() == unicodedata.normalize(
        "NFKC", destination.name
    ).casefold() and temporary.parent == destination.parent:
        raise ValueError("Source temporaire et destination identiques")

    temp_parent_handle = destination_parent_handle = source_handle = published_handle = None
    try:
        temp_parent_handle = _open_directory_chain(kernel32, ntdll, temporary.parent)
        destination_parent_handle = _open_directory_chain(kernel32, ntdll, destination.parent, require_add_file=True)
        temp_parent_info = _info(kernel32, temp_parent_handle)
        destination_parent_info = _info(kernel32, destination_parent_handle)
        if _identity(temp_parent_info) != _identity(destination_parent_info):
            raise ValueError("Le fichier temporaire doit être dans le même répertoire que la destination")

        source_handle = _open_relative(
            kernel32, ntdll, temp_parent_handle, temporary.name,
            _DELETE | _FILE_READ_DATA | _FILE_WRITE_DATA | _FILE_READ_ATTRIBUTES | _FILE_WRITE_ATTRIBUTES | _SYNCHRONIZE,
            _FILE_SHARE_READ,
            _FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
        )
        source_info = _info(kernel32, source_handle)
        if _is_directory(source_info) or _is_reparse(source_info):
            raise OSError("Le temporaire doit être un fichier régulier sans reparse point")
        if (int(source_info.nFileSizeHigh) << 32) | int(source_info.nFileSizeLow) <= 0:
            raise ValueError("Fichier temporaire absent ou vide")
        if not kernel32.FlushFileBuffers(wintypes.HANDLE(source_handle)):
            _win32_error("Synchronisation du fichier temporaire impossible")

        try:
            _create_exclusive_link(
                ntdll, source_handle, destination_parent_handle, destination.name
            )
        except FileExistsError:
            raise FileExistsError(17, "Destination existante; aucune donnée remplacée", str(original_destination)) from None

        published_handle = _open_relative(
            kernel32, ntdll, destination_parent_handle, destination.name,
            _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
            _FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
        )
        published_info = _info(kernel32, published_handle)
        if _is_directory(published_info) or _is_reparse(published_info) or (
            _identity(published_info) != _identity(source_info)
        ):
            raise RuntimeError("Entrée publiée substituée ou identité incohérente; revue manuelle requise")

        _verify_path_still_uses_directory(
            kernel32, ntdll, temporary.parent, temp_parent_handle
        )
        _verify_path_still_uses_directory(
            kernel32, ntdll, destination.parent, destination_parent_handle
        )
        return original_destination
    finally:
        for handle in (
            published_handle, source_handle,
            destination_parent_handle, temp_parent_handle,
        ):
            if handle is not None:
                _close(kernel32, handle)
