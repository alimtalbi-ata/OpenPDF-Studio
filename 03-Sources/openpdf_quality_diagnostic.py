"""V36.0: evidence-based diagnosis; no claim of conversion improvement. Author: Abdelhalim Talbi."""
from pathlib import Path
import json,statistics

def diagnose(rows, *, threshold=0.02):
    if not 0 <= threshold <= 1: raise ValueError('Invalid MAE threshold')
    output=[]
    for row in rows:
        mae=row.get('visual_mae'); recall=row.get('word_recall'); delta=row.get('page_delta')
        flags=[]
        if row.get('execution') != 'PASS': flags.append('conversion_failed')
        if mae is None: flags.append('visual_not_measured')
        elif not isinstance(mae,(int,float)) or not 0 <= mae <= 1: raise ValueError('Invalid MAE')
        elif mae > threshold: flags.append('visual_difference_above_threshold')
        if recall is None: flags.append('lexical_not_measured')
        elif recall < 0.99: flags.append('lexical_loss')
        if delta is None: flags.append('pagination_not_measured')
        elif delta != 0: flags.append('page_count_changed')
        output.append({**row,'flags':flags,'needs_review':bool(flags)})
    ranked=sorted(output,key=lambda r: (r.get('visual_mae') is None,-(r.get('visual_mae') or 0)))
    measured=[r['visual_mae'] for r in output if r.get('visual_mae') is not None]
    return {'schema':'openpdf-diagnostic-v1','threshold':threshold,'cases':len(output),'review_count':sum(r['needs_review'] for r in output),'mean_mae':round(statistics.mean(measured),6) if measured else None,'ranked_cases':ranked,'interpretation':'Threshold is a triage heuristic, not a validated quality acceptance criterion. Image mismatch cause remains unverified.'}

def from_scores(path):
    data=json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(data.get('rows'),list):raise ValueError('Invalid scores report')
    return diagnose(data['rows'])

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('scores');parser.add_argument('--output',required=True);parser.add_argument('--threshold',type=float,default=0.02)
    a=parser.parse_args(); report=diagnose(json.loads(Path(a.scores).read_text(encoding='utf8'))['rows'],threshold=a.threshold)
    Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print('Cases:',report['cases'],'Review:',report['review_count'],'Mean MAE:',report['mean_mae'])
