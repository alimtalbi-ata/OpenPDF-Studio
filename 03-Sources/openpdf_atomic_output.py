"""Exclusive PDF publication with directory-handle anchoring on POSIX.

V550 walks the destination parent with openat/O_NOFOLLOW-style operations and
publishes relative to the pinned directory descriptor. This prevents an
ancestor from being swapped for a symlink/junction between path preflight and
publication on supported POSIX systems. The standard-library Windows path is
kept compatible and rechecks reparse points, but is not claimed to eliminate
all Windows TOCTOU races.
Author: Abdelhalim Talbi.
"""
import os
import stat
import sys
from pathlib import Path


def _absolute(path):
    value = Path(path).expanduser()
    if not value.is_absolute():
        value = Path.cwd() / value
    return value


def _same_inode(left, right):
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


_HAS_DIRFD_PUBLICATION = (
    os.name == "posix"
    and all(function in os.supports_dir_fd for function in (os.open, os.link, os.stat))
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
)
_HAS_PROC_FD_LINK = (
    _HAS_DIRFD_PUBLICATION
    and sys.platform.startswith("linux")
    and Path("/proc/self/fd").is_dir()
    and os.link in os.supports_follow_symlinks
)


def _supports_anchored_publication():
    """Whether the running platform exposes the primitives required by V550."""
    return _HAS_DIRFD_PUBLICATION


def _link_open_inode(source_fd, temporary_name, destination_name, source_dir_fd, destination_dir_fd):
    """Link the already-open inode when Linux procfs supports it.

    `/proc/self/fd/N` keeps the source bound to the opened handle even if the
    temporary pathname is replaced after `open`. Other POSIX systems still use
    no-follow linkat-by-name plus post-publication inode verification.
    """
    if _HAS_PROC_FD_LINK:
        os.link(
            f"/proc/self/fd/{source_fd}", destination_name,
            dst_dir_fd=destination_dir_fd, follow_symlinks=True,
        )
    else:
        os.link(
            temporary_name, destination_name,
            src_dir_fd=source_dir_fd, dst_dir_fd=destination_dir_fd,
            follow_symlinks=False,
        )


def _open_directory_chain(directory):
    """Open a path one directory component at a time without following links.

    The returned descriptor owns the final directory handle. Intermediate
    descriptors are closed. `..` is processed by moving back through the open
    descriptor stack, so a symlink before `..` cannot be hidden by normalization.
    """
    path = _absolute(directory)
    if path.anchor != os.sep:
        raise OSError("Publication ancrée indisponible pour ce type de chemin")
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    )
    stack = []
    try:
        stack.append(os.open(os.sep, directory_flags))
        for component in path.parts[1:]:
            if component in ("", "."):
                continue
            if component == "..":
                if len(stack) > 1:
                    os.close(stack.pop())
                continue
            child = os.open(component, directory_flags, dir_fd=stack[-1])
            try:
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise OSError("Composant parent non répertoire")
            except BaseException:
                os.close(child)
                raise
            stack.append(child)
        result = stack.pop()
        for descriptor in reversed(stack):
            os.close(descriptor)
        return result
    except BaseException:
        for descriptor in reversed(stack):
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise


def _directory_identity(descriptor):
    info = os.fstat(descriptor)
    if not stat.S_ISDIR(info.st_mode):
        raise OSError("Handle de destination non répertoire")
    return info.st_dev, info.st_ino


def _verify_path_still_uses_directory(path, descriptor):
    try:
        current = _open_directory_chain(path)
    except (OSError, ValueError, RuntimeError) as exc:
        raise RuntimeError(
            "Dossier de publication déplacé ou remplacé pendant l'opération; vérification manuelle requise"
        ) from exc
    try:
        if _directory_identity(current) != _directory_identity(descriptor):
            raise RuntimeError(
                "Dossier de publication déplacé ou remplacé pendant l'opération; vérification manuelle requise"
            )
    finally:
        os.close(current)


def _publish_posix(temporary, destination, original_destination):
    if not _supports_anchored_publication():
        raise OSError(
            "Publication ancrée indisponible sur ce système; aucune sortie publiée"
        )

    temporary_parent_fd = destination_parent_fd = source_fd = None
    try:
        temporary_parent_fd = _open_directory_chain(temporary.parent)
        destination_parent_fd = _open_directory_chain(destination.parent)
        temporary_parent_identity = _directory_identity(temporary_parent_fd)
        destination_parent_identity = _directory_identity(destination_parent_fd)
        if temporary_parent_identity != destination_parent_identity:
            raise ValueError(
                "Le fichier temporaire doit être dans le même dossier que la destination"
            )
        if temporary.name == destination.name:
            raise ValueError("Source temporaire et destination identiques")

        source_flags = os.O_RDWR | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        source_fd = os.open(temporary.name, source_flags, dir_fd=temporary_parent_fd)
        source_info = os.fstat(source_fd)
        if not stat.S_ISREG(source_info.st_mode) or source_info.st_size <= 0:
            raise ValueError("Sortie temporaire absente, non régulière ou vide")

        # Confirm the name still identifies the opened inode before syncing.
        named_info = os.stat(
            temporary.name, dir_fd=temporary_parent_fd, follow_symlinks=False
        )
        if not stat.S_ISREG(named_info.st_mode) or not _same_inode(source_info, named_info):
            raise RuntimeError("Fichier temporaire remplacé; publication refusée")
        os.fsync(source_fd)

        try:
            _link_open_inode(
                source_fd, temporary.name, destination.name,
                temporary_parent_fd, destination_parent_fd,
            )
        except FileExistsError:
            raise FileExistsError(
                f"Destination existante : {original_destination}"
            ) from None
        except OSError as exc:
            raise OSError(
                "Publication exclusive ancrée indisponible; aucune réussite revendiquée"
            ) from exc

        # Verify the just-published directory entry is the inode opened above.
        # On mismatch, leave the entry for manual review rather than risk deleting
        # another process's replacement by name.
        published_info = os.stat(
            destination.name, dir_fd=destination_parent_fd, follow_symlinks=False
        )
        if not stat.S_ISREG(published_info.st_mode) or not _same_inode(source_info, published_info):
            raise RuntimeError(
                "Entrée temporaire remplacée pendant la publication; destination à examiner"
            )
        os.fsync(destination_parent_fd)

        _verify_path_still_uses_directory(temporary.parent, temporary_parent_fd)
        _verify_path_still_uses_directory(destination.parent, destination_parent_fd)
        return original_destination
    finally:
        for descriptor in (source_fd, destination_parent_fd, temporary_parent_fd):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def _publish_path_based(temporary, destination, original_destination):
    """Compatibility path for Windows; no full TOCTOU guarantee is claimed."""
    from openpdf_destination_path_guard_v549 import guard_destination_path

    temporary = guard_destination_path(temporary, allow_existing=True)
    destination = guard_destination_path(destination, allow_existing=True)
    if not temporary.is_file() or temporary.stat().st_size <= 0:
        raise ValueError("Sortie temporaire absente ou vide")
    try:
        if not os.path.samefile(temporary.parent, destination.parent):
            raise ValueError(
                "Le fichier temporaire doit être dans le même dossier que la destination"
            )
    except OSError as exc:
        raise ValueError("Dossier de publication inaccessible") from exc
    with temporary.open("r+b") as stream:
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, destination, follow_symlinks=False)
    except FileExistsError:
        raise FileExistsError(f"Destination existante : {original_destination}") from None
    except OSError as exc:
        raise OSError(
            "Publication exclusive indisponible sur ce volume; aucune réussite revendiquée"
        ) from exc
    try:
        source_info = temporary.stat()
        published_info = destination.stat(follow_symlinks=False)
        if not stat.S_ISREG(published_info.st_mode) or not _same_inode(source_info, published_info):
            raise RuntimeError("Destination modifiée pendant la publication; vérification manuelle requise")
    except OSError as exc:
        raise RuntimeError("Publication ambiguë; vérification manuelle requise") from exc
    return original_destination


def publish_exclusive(temporary, destination):
    """Publish a completed same-directory temporary without replacing any file.

    On supported POSIX filesystems, parent traversal is anchored to open
    directory handles and each component is opened without following symlinks.
    A path swap is detected after publication; the destination is deliberately
    left for manual review if a safe, identity-preserving rollback cannot be
    proven. Windows keeps the reparse-point preflight but does not claim complete
    TOCTOU elimination because the Python standard library lacks equivalent
    portable handle-relative link APIs there.
    The caller owns temporary cleanup.
    """
    original_destination = Path(destination)
    temporary_path = _absolute(temporary)
    destination_path = _absolute(destination)
    if not temporary_path.name or not destination_path.name:
        raise ValueError("Chemin de publication invalide")
    if os.name == "posix":
        return _publish_posix(temporary_path, destination_path, original_destination)
    if os.name == "nt":
        # V551 uses native handle-relative publication; never downgrade silently.
        from openpdf_windows_handle_publish_v551 import publish_exclusive_windows
        return publish_exclusive_windows(temporary_path, destination_path)
    return _publish_path_based(temporary_path, destination_path, original_destination)
