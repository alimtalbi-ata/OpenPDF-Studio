"""Opt-in runtime import tracing for headless OpenPDF services. No UI initialization."""
import importlib, json, sys, traceback
from pathlib import Path

DEFAULT_MODULES = ('openpdf_operations','openpdf_navigation','openpdf_jobs','openpdf_dependency_audit')

def trace_imports(names=DEFAULT_MODULES):
    if isinstance(names, str):
        raise TypeError('names must be a sequence of module names')
    result={'requested':list(names),'loaded':{},'errors':{},'runtime_modules':[]}
    before=set(sys.modules)
    for name in names:
        if not name.startswith('openpdf_') or not name.isidentifier():
            result['errors'][name]='Rejected non-OpenPDF module name';continue
        try:
            module=importlib.import_module(name)
            result['loaded'][name]=str(getattr(module,'__file__','built-in'))
        except Exception as exc:
            result['errors'][name]=f'{type(exc).__name__}: {exc}'
    result['runtime_modules']=sorted(n for n in sys.modules.keys()-before if n.startswith('openpdf'))
    result['warning']='Only selected headless imports were traced; GUI, plugins and packaged execution not covered.'
    return result

def save_report(result, destination):
    p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    return p

if __name__=='__main__':
    print(json.dumps(trace_imports(),ensure_ascii=False,indent=2))
