"""Batch conversion benchmark with explicit failures and no invented quality scores. Author: Abdelhalim Talbi."""
from pathlib import Path
from dataclasses import asdict
import json,time,hashlib
from openpdf_roundtrip_v356 import qualify

def run_batch(corpus, *, formats=("docx","xlsx","pptx"), libreoffice=None, timeout=120, max_pages=10, runner=None):
    corpus=Path(corpus)
    if not corpus.is_dir(): raise ValueError("Corpus directory absent")
    if not formats or any(f not in ("docx","xlsx","pptx") for f in formats): raise ValueError("Unsupported Office format")
    files=sorted(corpus.glob("*.pdf"))
    if not files: raise ValueError("No PDF in corpus")
    run=runner or qualify
    results=[]
    for pdf in files:
        for fmt in formats:
            start=time.monotonic()
            try:
                report=run(pdf,office_format=fmt,libreoffice=libreoffice,timeout=timeout,max_pages=max_pages)
                evidence=asdict(report) if hasattr(report,"__dataclass_fields__") else dict(report)
                results.append({"source":pdf.name,"format":fmt,"status":"PASS","duration_s":round(time.monotonic()-start,3),"evidence":evidence})
            except Exception as exc:
                results.append({"source":pdf.name,"format":fmt,"status":"FAIL","duration_s":round(time.monotonic()-start,3),"error_type":type(exc).__name__,"error":str(exc)[:500]})
    return {"schema":"openpdf-batch-v1","corpus":str(corpus),"cases":len(results),"passed":sum(r["status"]=="PASS" for r in results),"failed":sum(r["status"]=="FAIL" for r in results),"results":results}

def save_report(report,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf8")
    return path

def markdown_summary(report):
    lines=["# OpenPDF Studio — Batch qualification", "",f"Cases: {report['cases']} | PASS: {report['passed']} | FAIL: {report['failed']}","", "| Source | Office | Status | Seconds |", "|---|---|---|---:|"]
    for r in report['results']:lines.append(f"| {r['source']} | {r['format']} | {r['status']} | {r['duration_s']:.3f} |")
    return "\n".join(lines)+"\n"

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("corpus");parser.add_argument("--output",default="batch-v358.json");parser.add_argument("--timeout",type=int,default=120);args=parser.parse_args()
    report=run_batch(args.corpus,timeout=args.timeout);save_report(report,args.output);print(markdown_summary(report));raise SystemExit(1 if report["failed"] else 0)
