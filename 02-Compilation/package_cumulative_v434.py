"""V43.4: verified, slim, atomic Windows ZIP with content-stability checks. Abdelhalim Talbi."""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

FOLDERS = ('01-Application', '02-Compilation', '03-Sources', '04-Tests-et-Qualification', '05-Documentation', '06-Historique', '07-Manifestes')
ROOT_FILES = {'README.md', 'LISEZ-MOI.md', 'VERSION.txt', 'BUILD-OPENPDF-WINDOWS.cmd'}
SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', 'build', 'dist', 'node_modules', 'site-packages', '.pytest_cache', '.mypy_cache', '.tox', '.idea', '.vscode'}
SKIP_FILES = {'.env', 'token.json', 'credentials.json', 'secrets.json', '.netrc', 'id_rsa', 'id_ed25519'}
SKIP_EXT = {'.pyc', '.pyo', '.log', '.tmp', '.bak', '.pem', '.p12', '.pfx', '.key', '.sqlite', '.db'}
INVENTORY = '07-Manifestes/RELEASE-FILES-SHA256.json'
MAX_FILES = 200000
MAX_UNCOMPRESSED = 8 * 1024**3
MAX_MEMBER = 4 * 1024**3


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def names(version):
    return (f'OpenPDF-Studio-V{version}-Setup.exe', f'OpenPDF-Studio-Portable-V{version}.exe', f'binary-manifest-v{version}.json', f'windows-installation-v{version}.json', 'windows-smoke-installer.json', 'windows-smoke-portable.json')


def safe_name(name):
    parts = name.split('/')
    reserved = {'con', 'prn', 'aux', 'nul'} | {f'com{i}' for i in range(1, 10)} | {f'lpt{i}' for i in range(1, 10)}
    if not name or name.startswith('/') or '\\' in name or ':' in name or any(c in '<>"?*|' for c in name) or any(ord(c) < 32 for c in name) or any(not p or p in ('.', '..') or p.rstrip(' .') != p or p.split('.')[0].casefold() in reserved for p in parts):
        raise ValueError('Unsafe ZIP member: ' + name)
    if parts[0] not in FOLDERS and (len(parts) != 1 or name not in ROOT_FILES):
        raise ValueError('Unexpected ZIP member root: ' + name)


def forbidden_member(name, version):
    """Apply the same security and slimming policy when verifying external ZIPs.

    SHA-256 alone is insufficient if an attacker regenerates the inventory.
    """
    parts = name.split('/')
    basename = parts[-1].casefold()
    if any(part.casefold() in SKIP_DIRS or part.casefold().startswith('.staging-') for part in parts[:-1]):
        return True
    if basename in SKIP_FILES or basename.startswith(('.env.', 'secrets.')):
        return True
    if Path(basename).suffix in SKIP_EXT or basename.endswith('~'):
        return True
    if parts[:2] == ['01-Application', 'release']:
        return True
    if parts[:2] == ['01-Application', 'binary']:
        return len(parts) != 3 or parts[-1] not in names(version)
    return False


def evidence(version, read, size):
    prefix = '01-Application/binary/'
    required = [prefix + x for x in names(version)]
    required += [f'05-Documentation/OpenPDF-Studio-V{version}-Guide.{ext}' for ext in ('docx', 'pdf')]
    for name in required:
        if size(name) <= 0:
            raise ValueError('Missing qualified Windows artifact or documentation: ' + name)
    if any(size(name) > 512 * 1024**2 for name in required[:2]) or any(size(name) > 32 * 1024**2 for name in required[2:]):
        raise ValueError('Oversized qualified artifact or documentation')
    manifest = json.loads(read(required[2]).decode('utf-8-sig'))
    if str(manifest.get('version')) != version or not isinstance(manifest.get('binaries'), list):
        raise ValueError('Stale binary manifest')
    for mode, filename in (('installer', names(version)[0]), ('portable', names(version)[1])):
        path = prefix + filename
        binary = read(path)
        if binary[:2] != b'MZ':
            raise ValueError('Invalid PE header: ' + filename)
        sha = hashlib.sha256(binary).hexdigest()
        entries = [x for x in manifest['binaries'] if isinstance(x, dict) and x.get('filename') == filename]
        if len(entries) != 1 or entries[0].get('sha256') != sha or entries[0].get('size_bytes') != size(path) or entries[0].get('pe_mz_header') is not True:
            raise ValueError('Unbound binary manifest: ' + filename)
        smoke = json.loads(read(prefix + f'windows-smoke-{mode}.json').decode('utf-8-sig'))
        checks = smoke.get('checks')
        if (str(smoke.get('version')) != version or smoke.get('mode') != mode or smoke.get('passed') is not True or smoke.get('artifact_name') != filename or smoke.get('artifact_sha256') != sha or not isinstance(checks, list) or len(checks) != 2 or any(not isinstance(c, dict) or c.get('passed') is not True for c in checks)):
            raise ValueError('Unbound Windows smoke: ' + mode)
    installation = json.loads(read(required[3]).decode('utf-8-sig'))
    if (str(installation.get('version')) != version or installation.get('passed') is not True or installation.get('artifact_name') != names(version)[0] or installation.get('artifact_sha256') != hashlib.sha256(read(required[0])).hexdigest() or not isinstance(installation.get('steps'), list) or not {'silent_install_pass', 'installed_launch_pass', 'silent_uninstall_pass'}.issubset(set(installation['steps']))):
        raise ValueError('Unbound Windows installation evidence')
    if read(required[-1])[:5] != b'%PDF-':
        raise ValueError('Invalid PDF documentation')
    with zipfile.ZipFile(__import__('io').BytesIO(read(required[-2]))) as doc:
        if 'word/document.xml' not in doc.namelist() or doc.testzip() is not None:
            raise ValueError('Invalid DOCX documentation')
    return set(required)


def payload(root, version):
    for folder in FOLDERS:
        base = root / folder
        if not base.is_dir() or base.is_symlink():
            raise ValueError('Missing or linked mandatory folder: ' + folder)
        for current, dirs, files in os.walk(base, followlinks=False):
            current = Path(current)
            for dirname in list(dirs):
                rel = (current / dirname).relative_to(root)
                if dirname.casefold() in SKIP_DIRS or dirname.casefold().startswith('.staging-') or rel.parts[:2] == ('01-Application', 'release'):
                    dirs.remove(dirname)
                elif (current / dirname).is_symlink():
                    raise ValueError('Unsafe directory symlink: ' + str(rel))
            dirs.sort()
            for filename in sorted(files):
                path = current / filename
                rel = path.relative_to(root)
                lower = filename.casefold()
                if rel.as_posix() in (INVENTORY, '07-Manifestes/RELEASE-QUALIFICATION-LIMITS.txt'):
                    continue
                if forbidden_member(rel.as_posix(), version):
                    continue
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Unsafe payload symlink: ' + str(rel))
                safe_name(rel.as_posix())
                yield rel.as_posix(), path
    for filename in sorted(ROOT_FILES):
        path = root / filename
        if path.is_symlink():
            raise ValueError('Unsafe root symlink: ' + filename)
        if path.is_file():
            yield filename, path


def verify(path):
    with zipfile.ZipFile(path) as archive:
        all_infos = archive.infolist()
        directories = set()
        for entry in all_infos:
            if entry.is_dir():
                safe_name(entry.filename.rstrip('/'))
                key = entry.filename.casefold()
                if key in directories:
                    raise ValueError('Duplicate ZIP directory: ' + entry.filename)
                if stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFLNK:
                    raise ValueError('Symlink ZIP directory: ' + entry.filename)
                directories.add(key)
        infos = [x for x in all_infos if not x.is_dir()]
        if len(infos) > MAX_FILES or sum(x.file_size for x in infos) > MAX_UNCOMPRESSED or any(x.file_size > MAX_MEMBER for x in infos):
            raise ValueError('ZIP safety limits exceeded')
        members = {}
        folded = set()
        for info in infos:
            safe_name(info.filename)
            if info.filename.casefold() in folded or (info.filename + '/').casefold() in directories:
                raise ValueError('Duplicate ZIP member: ' + info.filename)
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError('Symlink ZIP member: ' + info.filename)
            folded.add(info.filename.casefold())
            members[info.filename] = info
        # Reject paths that use a regular file as a parent directory. Such ZIPs
        # cannot be extracted consistently on Windows or POSIX.
        for name in members:
            parents = name.split('/')[:-1]
            for index in range(1, len(parents) + 1):
                if '/'.join(parents[:index]).casefold() in folded:
                    raise ValueError('ZIP file/directory collision: ' + name)
        if INVENTORY not in members or members[INVENTORY].file_size > 32 * 1024**2:
            raise ValueError('Integrity inventory missing or oversized')
        rows = json.loads(archive.read(INVENTORY).decode('utf-8-sig'))
        if not isinstance(rows, list):
            raise ValueError('Invalid integrity inventory')
        recorded = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('path'), str) or type(row.get('bytes')) is not int or row['bytes'] < 0 or not re.fullmatch('[0-9a-f]{64}', str(row.get('sha256'))):
                raise ValueError('Invalid integrity inventory record')
            name = row['path']
            safe_name(name)
            if name == INVENTORY or name in recorded or name not in members or members[name].file_size != row['bytes']:
                raise ValueError('Missing or duplicated inventory member: ' + name)
            h = hashlib.sha256()
            with archive.open(members[name]) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            if h.hexdigest() != row['sha256']:
                raise ValueError('ZIP member SHA256 mismatch: ' + name)
            recorded[name] = row
        if set(recorded) | {INVENTORY} != set(members):
            raise ValueError('ZIP contains files not represented in inventory')
        if 'VERSION.txt' not in members:
            raise ValueError('Missing ZIP version')
        version = archive.read('VERSION.txt').decode('utf-8-sig').strip()
        if not re.fullmatch(r'\d+\.\d+', version):
            raise ValueError('Invalid ZIP version')
        for name in members:
            if name not in (INVENTORY, '07-Manifestes/RELEASE-QUALIFICATION-LIMITS.txt') and forbidden_member(name, version):
                raise ValueError('Forbidden release payload member: ' + name)
        required = evidence(version, archive.read, lambda name: members[name].file_size if name in members else 0)
        if any(x.startswith('01-Application/binary/') and x not in required for x in members):
            raise ValueError('Unexpected binary in ZIP')
    return {'verified_files': len(rows), 'archive_bytes': Path(path).stat().st_size, 'archive_sha256': digest(path)}


def package(root, commit=''):
    root = Path(root).resolve(strict=True)
    version = (root / 'VERSION.txt').read_text(encoding='utf-8-sig').strip()
    if not re.fullmatch(r'\d+\.\d+', version):
        raise ValueError('Invalid release version')
    binary = root / '01-Application' / 'binary'
    if binary.is_symlink():
        raise ValueError('Unsafe binary directory')
    evidence(version, lambda name: (root / name).read_bytes(), lambda name: (root / name).stat().st_size if (root / name).is_file() else 0)
    release = root / '01-Application' / 'release'
    if release.is_symlink():
        raise ValueError('Unsafe release directory symlink')
    release.mkdir(exist_ok=True)
    target = release / f'OpenPDF Studio V{version} --- Windows Cumulative.zip'
    fd, partial = tempfile.mkstemp(prefix='.openpdf-', suffix='.partial', dir=release)
    os.close(fd)
    try:
        seen = set()
        rows = []
        uncompressed = 0
        with zipfile.ZipFile(partial, 'w', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            for name, path in payload(root, version):
                if name.casefold() in seen:
                    raise ValueError('Case-insensitive payload collision: ' + name)
                seen.add(name.casefold())
                if len(rows) >= MAX_FILES:
                    raise ValueError('ZIP safety limits exceeded before writing')
                file_size = path.stat().st_size
                uncompressed += file_size
                if file_size > MAX_MEMBER or uncompressed > MAX_UNCOMPRESSED:
                    raise ValueError('ZIP safety limits exceeded before writing')
                # Stronger than inode/size/mtime: reject in-place edits that restore metadata.
                expected_digest = digest(path)
                info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                h = hashlib.sha256()
                size = 0
                before = path.stat()
                with path.open('rb') as src, archive.open(info, 'w', force_zip64=True) as dst:
                    for block in iter(lambda: src.read(1024 * 1024), b''):
                        size += len(block)
                        if size > MAX_MEMBER:
                            raise ValueError('Oversized release payload: ' + name)
                        h.update(block)
                        dst.write(block)
                after = path.stat()
                if ((before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino)
                    or size != before.st_size or h.hexdigest() != expected_digest
                    or digest(path) != expected_digest):
                    raise RuntimeError('Source changed during packaging: ' + name)
                rows.append({'path': name, 'bytes': size, 'sha256': h.hexdigest()})
            qualification = ('Author: Abdelhalim Talbi\nCommit: ' + (commit or 'unknown') + '\nWindows CI tests are automated; interactive UI inspection not performed.\n').encode()
            extra = '07-Manifestes/RELEASE-QUALIFICATION-LIMITS.txt'
            if extra in seen:
                raise ValueError('Duplicate generated qualification file')
            archive.writestr(extra, qualification)
            rows.append({'path': extra, 'bytes': len(qualification), 'sha256': hashlib.sha256(qualification).hexdigest()})
            archive.writestr(INVENTORY, json.dumps(sorted(rows, key=lambda x: x['path']), indent=2).encode())
        result = verify(partial)
        os.replace(partial, target)
        return {'path': str(target), 'version': version, **result}
    finally:
        if os.path.exists(partial):
            os.unlink(partial)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--commit', default=os.environ.get('GITHUB_SHA', ''))
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.verify) if args.verify else package(args.root, args.commit), indent=2))

# Compatibility names for regression tests.
ROOT_FOLDERS = FOLDERS
_binary_names = names
_sha256 = digest
_validate_zip_name = safe_name
verify_archive = verify
