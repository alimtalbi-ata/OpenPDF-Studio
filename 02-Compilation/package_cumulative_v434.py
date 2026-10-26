"""V43.4: verified, slim, atomic Windows ZIP with content-stability checks. Abdelhalim Talbi."""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import unicodedata
import zipfile
from pathlib import Path

FOLDERS = ('01-Application', '02-Compilation', '03-Sources', '04-Tests-et-Qualification', '05-Documentation', '06-Historique', '07-Manifestes')
OPTIONAL_FOLDERS = ('.github',)
ROOT_FILES = {'README.md', 'LISEZ-MOI.md', 'VERSION.txt', 'BUILD-OPENPDF-WINDOWS.cmd', '.gitattributes'}
SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', 'build', 'dist', 'node_modules', 'site-packages', '.pytest_cache', '.mypy_cache', '.tox', '.idea', '.vscode'}
SKIP_FILES = {'.env', 'token.json', 'credentials.json', 'secrets.json', '.netrc', 'id_rsa', 'id_ed25519'}
SKIP_EXT = {'.pyc', '.pyo', '.log', '.tmp', '.bak', '.pem', '.p12', '.pfx', '.key', '.sqlite', '.db'}
INVENTORY = '07-Manifestes/RELEASE-FILES-SHA256.json'
CHECKSUMS = '07-Manifestes/SHA256SUMS.txt'
MAX_FILES = 200000
MAX_UNCOMPRESSED = 8 * 1024**3
MAX_MEMBER = 4 * 1024**3


def write_fixed_member(archive, name, content):
    """Write generated metadata with deterministic ZIP timestamps and modes."""
    info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    archive.writestr(info, content)

def render_sha256_sums(rows):
    """Render the current release checksum list from verified inventory rows.

    SHA256SUMS.txt excludes itself and the JSON inventory to avoid circular hashes;
    the JSON inventory includes the hash of SHA256SUMS.txt.
    """
    selected = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid SHA256SUMS inventory row')
        name = row.get('path')
        sha = row.get('sha256')
        if not isinstance(name, str) or not re.fullmatch('[0-9a-f]{64}', str(sha)):
            raise ValueError('Invalid SHA256SUMS inventory entry')
        safe_name(name)
        if name in (CHECKSUMS, INVENTORY):
            continue
        key = archive_path_key(name)
        if key in seen:
            raise ValueError('Duplicate SHA256SUMS path after normalization (NFKC/casefold): ' + name)
        seen.add(key)
        selected.append((name, sha))
    return ''.join(f'{sha}  {name}\n' for name, sha in sorted(selected))

def validate_sha256_sums(actual, rows):
    """Require SHA256SUMS.txt to match every non-circular inventory member."""
    if not isinstance(actual, bytes) or actual != render_sha256_sums(rows).encode('ascii'):
        raise ValueError('SHA256SUMS.txt does not match the current release inventory')


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
    if parts[0] not in FOLDERS + OPTIONAL_FOLDERS and (len(parts) != 1 or name not in ROOT_FILES):
        raise ValueError('Unexpected ZIP member root: ' + name)


def archive_path_key(name):
    """Return a Windows-aware archive-path identity, rejecting normalized syntax changes.

    Compatibility characters must not turn into path separators, traversal segments,
    reserved device names, or other forbidden Windows syntax after validation.
    NFKC plus casefold is used only as a collision key; the original stored name is
    preserved in the manifest and archive.
    """
    safe_name(name)
    normalized = unicodedata.normalize('NFKC', name)
    if normalized.count('/') != name.count('/'):
        raise ValueError('ZIP path separators change under Unicode normalization: ' + name)
    safe_name(normalized)
    return normalized.casefold()


def forbidden_member(name, version):
    """Apply the same security and slimming policy when verifying external ZIPs.

    SHA-256 alone is insufficient if an attacker regenerates the inventory.
    Compatibility Unicode is normalized before checking security exclusions.
    """
    parts = unicodedata.normalize('NFKC', name).split('/')
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



SMOKE_ARGUMENTS = (
    '--self-test',
    '--functional-self-test',
    '--ocr-runtime-self-test',
)


def validate_smoke_receipt(smoke, *, version, mode, filename, sha256):
    """Validate the exact native smoke contract required by this release.

    V51.4 builds execute the OCR runtime smoke in addition to the startup and
    functional checks. A two-check receipt is stale and must not qualify the
    cumulative package. Only bounded metadata is examined here; stdout/stderr
    remain archived as evidence, never rendered into user-facing diagnostics.
    """
    if (type(smoke) is not dict
            or str(smoke.get('version')) != version
            or smoke.get('mode') != mode
            or smoke.get('passed') is not True
            or smoke.get('artifact_name') != filename
            or smoke.get('artifact_sha256') != sha256):
        raise ValueError('Unbound Windows smoke: ' + mode)
    checks = smoke.get('checks')
    if type(checks) is not list or len(checks) != len(SMOKE_ARGUMENTS):
        raise ValueError('Incomplete Windows smoke checks: ' + mode)
    observed = []
    for check in checks:
        if type(check) is not dict:
            raise ValueError('Malformed Windows smoke check: ' + mode)
        argument = check.get('argument')
        if type(argument) is not str or argument not in SMOKE_ARGUMENTS or argument in observed:
            raise ValueError('Unexpected or duplicated Windows smoke check: ' + mode)
        if (type(check.get('exit_code')) is not int or check.get('exit_code') != 0
                or check.get('passed') is not True or check.get('timed_out') is not False
                or type(check.get('stdout')) is not str
                or type(check.get('stderr')) is not str):
            raise ValueError('Failed Windows smoke check: ' + mode)
        observed.append(argument)
    if set(observed) != set(SMOKE_ARGUMENTS):
        raise ValueError('Missing required Windows smoke check: ' + mode)
    return True


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
        validate_smoke_receipt(smoke, version=version, mode=mode,
                               filename=filename, sha256=sha)
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
    seen = set()
    for folder in FOLDERS + OPTIONAL_FOLDERS:
        base = root / folder
        if folder in OPTIONAL_FOLDERS and not base.exists() and not base.is_symlink():
            continue
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
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Unsafe payload symlink: ' + str(rel))
                candidate = rel.as_posix()
                safe_name(candidate)
                archive_path_key(candidate)
                if candidate == CHECKSUMS:
                    # Preserve the old repository list but label it honestly; generate a new
                    # current-release SHA256SUMS.txt from this archive's measured contents.
                    output_name = '07-Manifestes/SHA256SUMS-LEGACY-NOT-CURRENT.txt'
                    output_key = archive_path_key(output_name)
                    if output_key in seen:
                        raise ValueError('Unicode-normalized payload collision: ' + output_name)
                    seen.add(output_key)
                    yield output_name, path
                    continue
                if candidate in (INVENTORY, '07-Manifestes/RELEASE-QUALIFICATION-LIMITS.txt'):
                    continue
                if forbidden_member(candidate, version):
                    continue
                if path.is_symlink() or not path.is_file():
                    raise ValueError('Unsafe payload symlink: ' + str(rel))
                key = archive_path_key(candidate)
                if key in seen:
                    raise ValueError('Unicode-normalized payload collision: ' + candidate)
                seen.add(key)
                yield candidate, path
    for filename in sorted(ROOT_FILES):
        path = root / filename
        if path.is_symlink():
            raise ValueError('Unsafe root symlink: ' + filename)
        if path.is_file():
            key = archive_path_key(filename)
            if key in seen:
                raise ValueError('Unicode-normalized payload collision: ' + filename)
            seen.add(key)
            yield filename, path


def verify(path):
    with zipfile.ZipFile(path) as archive:
        all_infos = archive.infolist()
        directories = set()
        directory_names = []
        for entry in all_infos:
            if entry.is_dir():
                directory_name = entry.filename.rstrip('/')
                safe_name(directory_name)
                key = archive_path_key(directory_name)
                if key in directories:
                    raise ValueError('Duplicate ZIP directory after Unicode normalization: ' + entry.filename)
                if stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFLNK:
                    raise ValueError('Symlink ZIP directory: ' + entry.filename)
                directories.add(key)
                directory_names.append(directory_name)
        infos = [x for x in all_infos if not x.is_dir()]
        if len(infos) > MAX_FILES or sum(x.file_size for x in infos) > MAX_UNCOMPRESSED or any(x.file_size > MAX_MEMBER for x in infos):
            raise ValueError('ZIP safety limits exceeded')
        members = {}
        folded = set()
        for info in infos:
            safe_name(info.filename)
            key = archive_path_key(info.filename)
            if key in folded or key in directories:
                raise ValueError('Duplicate ZIP member after Unicode normalization: ' + info.filename)
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError('Symlink ZIP member: ' + info.filename)
            folded.add(key)
            members[info.filename] = info
        # Check both files and explicit directories: a regular file may otherwise
        # alias a parent of a child even when no explicit ZIP directory exists.
        for name in list(members) + directory_names:
            normalized = unicodedata.normalize('NFKC', name)
            parents = normalized.split('/')[:-1]
            for index in range(1, len(parents) + 1):
                parent_key = archive_path_key('/'.join(parents[:index]))
                if parent_key in folded:
                    raise ValueError('ZIP file/directory collision: ' + name)
        if INVENTORY not in members or CHECKSUMS not in members or members[INVENTORY].file_size > 32 * 1024**2:
            raise ValueError('Integrity inventory or current checksum list missing/oversized')
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
        validate_sha256_sums(archive.read(CHECKSUMS), rows)
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
            write_fixed_member(archive, extra, qualification)
            rows.append({'path': extra, 'bytes': len(qualification), 'sha256': hashlib.sha256(qualification).hexdigest()})
            sums = render_sha256_sums(rows).encode('ascii')
            write_fixed_member(archive, CHECKSUMS, sums)
            rows.append({'path': CHECKSUMS, 'bytes': len(sums), 'sha256': hashlib.sha256(sums).hexdigest()})
            write_fixed_member(archive, INVENTORY, json.dumps(sorted(rows, key=lambda x: x['path']), indent=2).encode())
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
