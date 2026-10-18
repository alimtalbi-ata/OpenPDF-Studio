"""Offline dependency and environment preflight for the V25.8 Windows launcher."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys


def inspect_environment(base=None):
    base = Path(base or Path(__file__).resolve().parent)
    modules = {name: importlib.util.find_spec(name) is not None for name in ('tkinter', 'hashlib', 'zipfile')}
    files = {name: (base / name).is_file() for name in ('audit_assistant_v257.py', 'audit_dossier_v256.py', 'verify_proof_audit_v254.py')}
    issues = []
    if sys.version_info < (3, 9): issues.append('Python 3.9 ou plus récent requis')
    for name, available in modules.items():
        if not available: issues.append('Module Python absent : ' + name)
    for name, available in files.items():
        if not available: issues.append('Fichier applicatif absent : ' + name)
    if os.name != 'nt': issues.append('Environnement non Windows : qualification Windows native non réalisée')
    return {'schema': 'openpdf-windows-preflight-v25.8', 'python': platform.python_version(),
            'platform': platform.system(), 'windows': os.name == 'nt', 'modules': modules,
            'files': files, 'ready': not any('requis' in x or 'absent' in x for x in issues),
            'warnings': issues, 'gui_runtime_tested': False}


def main():
    parser = argparse.ArgumentParser(description='Contrôle hors ligne des prérequis OpenPDF Studio')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = inspect_environment()
    if args.json: print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('OpenPDF Studio V25.8 — prérequis : ' + ('OK' if result['ready'] else 'ECHEC'))
        print('Python :', result['python'], '| Plateforme :', result['platform'])
        for warning in result['warnings']: print(' -', warning)
        print('Test d’ouverture graphique : non exécuté')
    return 0 if result['ready'] else 1


if __name__ == '__main__': raise SystemExit(main())
