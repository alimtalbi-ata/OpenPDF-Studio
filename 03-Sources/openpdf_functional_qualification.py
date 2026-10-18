"""Real PDF operations qualification, isolated synthetic inputs. Author: Abdelhalim Talbi."""
from pathlib import Path
import tempfile, json, time, traceback
import fitz
from openpdf_operations import run_operation

def run_suite():
    cases=[]
    with tempfile.TemporaryDirectory(prefix="openpdf-qualification-") as td:
        d=Path(td); a=d/'a.pdf'; b=d/'b.pdf'
        for path, texts in [(a,['Page alpha','Page beta','Page gamma']),(b,['Page delta'])]:
            pdf=fitz.open()
            for value in texts:
                page=pdf.new_page(); page.insert_text((60,70),value)
            pdf.save(path);pdf.close()
        def check(name, op, inputs, dest, expected, **kw):
            started=time.monotonic()
            try:
                result=run_operation(op,inputs,dest,**kw)
                with fitz.open(dest) as pdf:
                    found=[p.get_text().strip() for p in pdf]
                    assert len(pdf)==len(expected),(len(pdf),len(expected))
                    for i,text in enumerate(expected):assert text in found[i],(i,text,found[i])
                cases.append({'case':name,'status':'PASS','seconds':round(time.monotonic()-started,4),'result_type':type(result).__name__})
            except Exception as e:cases.append({'case':name,'status':'FAIL','seconds':round(time.monotonic()-started,4),'error':str(e),'trace':traceback.format_exc()[-1000:]})
        check('merge','fusion',[a,b],d/'merged.pdf',['Page alpha','Page beta','Page gamma','Page delta'])
        check('extract','extraction',[a],d/'extract.pdf',['Page beta','Page gamma'],first=2,last=3)
        check('reorder','reorganisation',[a],d/'reorder.pdf',['Page gamma','Page alpha'],order='3,1')
        split_dir=d/'split';split_dir.mkdir()
        started=time.monotonic()
        try:
            receipt=run_operation('decoupage',[a],split_dir,chunk=2)
            assert len(receipt.outputs)==2
            actual=[]
            for output in receipt.outputs:
                with fitz.open(output) as pdf:actual.extend([page.get_text().strip() for page in pdf])
            assert actual==['Page alpha','Page beta','Page gamma'],actual
            cases.append({'case':'split-single','status':'PASS','files':len(receipt.outputs),'seconds':round(time.monotonic()-started,4)})
        except Exception as e:cases.append({'case':'split-single','status':'FAIL','error':str(e),'trace':traceback.format_exc()[-1000:]})
        # Compression is receipt-driven and may refuse publication when no gain; test this contract separately.
        started=time.monotonic()
        try:
            receipt=run_operation('compression',[a],d/'compressed.pdf',profile='smaller_only')
            published=bool(receipt.published)
            if published:
                with fitz.open(d/'compressed.pdf') as pdf:assert len(pdf)==3
            else:assert not (d/'compressed.pdf').exists()
            cases.append({'case':'compression-publication','status':'PASS','published':published,'seconds':round(time.monotonic()-started,4)})
        except Exception as e:cases.append({'case':'compression-publication','status':'FAIL','error':str(e),'trace':traceback.format_exc()[-1000:]})
    return {'version':'36.5','synthetic':True,'environment':'Linux / PyMuPDF; not Windows UI qualification','cases':cases,'passed':sum(c['status']=='PASS' for c in cases),'total':len(cases)}
if __name__=='__main__':
    report=run_suite();print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed']==report['total'] else 1)
