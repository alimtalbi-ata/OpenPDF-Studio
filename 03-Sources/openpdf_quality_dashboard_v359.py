"""Real batch quality dashboard: execution success is not conversion quality. Author: Abdelhalim Talbi."""
import json
from pathlib import Path
def summarize(report):
    out=[]
    for r in report["results"]:
        e=r.get("evidence") or {}; v=e.get("visual") or {}; s=e.get("structure") or {}
        out.append({"source":r["source"],"format":r["format"],"execution":r["status"],"visual_mae":v.get("mean_absolute_error"),"word_recall":s.get("word_recall"),"page_delta":s.get("page_delta"),"error":r.get("error")})
    return out
def markdown(rows):
    result=["# Real conversion results", "", "MAE lower is better; lexical recall higher is better. Execution PASS is not fidelity PASS.","", "| PDF | Format | Execution | Visual MAE | Word recall | Page delta |", "|---|---|---|---:|---:|---:|"]
    for r in rows:
        f=lambda x: "N/A" if x is None else str(x)
        result.append("| " + " | ".join(map(f,[r["source"],r["format"],r["execution"],r["visual_mae"],r["word_recall"],r["page_delta"]]))+" |")
    return "\n".join(result)+"\n"
if __name__=="__main__":
    import sys
    if len(sys.argv)!=2:raise SystemExit("Usage: python openpdf_quality_dashboard_v359.py batch.json")
    print(markdown(summarize(json.loads(Path(sys.argv[1]).read_text(encoding="utf8")))))
