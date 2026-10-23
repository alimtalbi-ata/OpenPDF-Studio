"""Streaming SHA-256 proof for staged PDF split outputs.
Author: Abdelhalim Talbi. A digest is integrity evidence, not an authenticity proof.
"""
import hashlib
import re
from pathlib import Path


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def valid_digest_list(digests, names):
    return (isinstance(digests, list) and len(digests) == len(names)
            and all(isinstance(d, str) and re.fullmatch(r'[0-9a-f]{64}', d)
                    for d in digests))


def verify_staged(stage, names, digests):
    if not valid_digest_list(digests, names):
        raise RuntimeError('Empreintes des sorties invalides')
    for name, expected in zip(names, digests):
        path = Path(stage) / name
        if path.is_symlink() or not path.is_file() or file_sha256(path) != expected:
            raise RuntimeError('Sortie de découpage modifiée : publication rejetée')
