"""Inspect actual Tk widgets; no fake screenshots or simulated button clicks."""
import argparse, json, sys
from datetime import datetime,timezone
from pathlib import Path

def inventory(root):
    widgets=[]
    def visit(w, depth=0):
        item={'class':w.winfo_class(),'path':str(w),'depth':depth}
        for prop in ('text','state','command'):
            try:
                value=w.cget(prop)
                if prop=='command':item['has_command']=bool(str(value))
                elif value:item[prop]=str(value)[:300]
            except Exception:pass
        widgets.append(item)
        for child in w.winfo_children():visit(child,depth+1)
    visit(root)
    return widgets

def audit(app_factory=None):
    result={'version':'29.4','platform':sys.platform,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'status':'FAIL'}
    if sys.platform!='win32':
        result['error']='Windows GUI audit requires Windows';return result
    app=None
    try:
        if app_factory is None:
            from openpdf_windows_v294 import OpenPDFStudio
            app_factory=OpenPDFStudio
        app=app_factory();app.update_idletasks();app.update()
        widgets=inventory(app)
        actionable=[w for w in widgets if w.get('has_command') and w.get('state','normal')!='disabled']
        result.update({'title':app.title(),'widgets':widgets,'widget_count':len(widgets),'actionable_count':len(actionable)})
        if not widgets or not actionable:raise RuntimeError('No actionable GUI controls discovered')
        result['status']='PASS'
    except Exception as exc:result['error']=f'{type(exc).__name__}: {exc}'
    finally:
        if app is not None:
            try:app.destroy()
            except Exception:pass
    return result

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='qualification-ui-v29.4.json');args=parser.parse_args(argv)
    report=audit();p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='widgets'},ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
